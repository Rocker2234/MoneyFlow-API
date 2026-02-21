from datetime import datetime

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from ..file_actions import get_reader, get_group
from ..filters import AccTransactionFilter
from ..models import FileAudit
from ..pagination import DefaultPagination
from ..serializers.account_serializers import *


class AccountViewSet(ModelViewSet):
    serializer_class = AccountSerializer
    pagination_class = DefaultPagination

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'acc_no', 'ifsc_code']
    ordering_fields = ['id', 'act_ind', 'min_bal']

    def get_queryset(self) -> QuerySet:
        return Account.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(account__id=kwargs['pk']).select_related('credit_card').count() > 0:
            return Response({'error': 'Account is accosiated with transactions!'}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='upload')
    def upload_transaction_file(self, request: Request, pk: int) -> Response:
        """
        Handles the upload of transaction files for a specific account. This method processes
        the uploaded file by validating the entries, checking for duplicates or conditions
        based on parameters, and creating new transaction records in the database.

        :param request: The HTTP request containing the uploaded file and additional upload
            parameters such as date format, parser selection, and grouping strategy.
            Should be of type Request.
        :param pk: The primary key of the account for which the transactions are being uploaded.
            Should be of type int.
        :return: A Response containing details of the uploaded file, the number of transactions
            created, or an error message in case of failure. Possible statuses include
            HTTP_201_CREATED for success, HTTP_422_UNPROCESSABLE_ENTITY for unmet conditions,
            and HTTP_500_INTERNAL_SERVER_ERROR for unexpected failures.
        """
        acc = self.get_object()

        serializer = TransactionFileUploadSerializer(data=request.data, context={'request': request, 'acc': acc})
        serializer.is_valid(raise_exception=True)

        dt_format = serializer.validated_data['dt_format']
        parser = serializer.validated_data['parser']
        is_future_only = serializer.validated_data['is_future_only']
        is_strict_future = serializer.validated_data['is_strict_future']

        uploaded_file = request.FILES.get('file')
        if uploaded_file is None:
            return Response({'error': 'No file provided!'}, status=status.HTTP_400_BAD_REQUEST)

        txns = []

        audit_log = FileAudit.objects.create(
            file_name=uploaded_file.name,
            to_id=acc.id,
            op_desc='ACC_TXN_UPLOAD',
            status='LOADING',
            op_args=f'Acc:{acc.id}, dt_format:{dt_format}, reader:{parser}, grouper:{request.data.get("grouper", "")}',
            user=request.user
        )

        try:
            reader = get_reader(uploaded_file, parser)
            latest_txn = Transaction.objects.filter(account=acc).order_by('-txn_date',
                                                                          '-id').first() if is_future_only else None
            found_match = False

            with transaction.atomic():
                for row in reader:
                    this_txn = Transaction(
                        account=acc,
                        txn_date=timezone.make_aware(datetime.strptime(row['txn_date'], dt_format),
                                                     ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz"))),
                        txn_desc=row['txn_desc'],
                        grp_name=get_group(serializer.validated_data['grouper'], row['txn_desc']),
                        opr_dt=timezone.make_aware(datetime.strptime(row['opr_dt'], dt_format),
                                                   ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz"))),
                        dbt_amount=row['dbt_amount'],
                        cr_amount=row['cr_amount'],
                        ref_num=row['ref_num'],
                        cf_amt=row['cf_amt'],
                        src_file=audit_log
                    )

                    # If user requested validation run tests until first match
                    if latest_txn and (not found_match):
                        if is_strict_future:    # Only insert the transactions after finding the latest uploaded transaction
                            found_match = (
                                    this_txn.cf_amt == str(latest_txn.cf_amt) and
                                    this_txn.txn_date == latest_txn.txn_date and
                                    this_txn.txn_desc == latest_txn.txn_desc
                            )
                            continue
                        elif is_future_only:    # Only insert transactions that's after the latest uploaded transaction
                            if this_txn.txn_date < latest_txn.txn_date:
                                continue
                            found_match = True
                    txns.append(this_txn)
                if len(txns) != 0:
                    Transaction.objects.bulk_create(txns)
                    audit_log.status = 'LOADED'
                    audit_log.save()
                else:
                    audit_log.status = 'NO TXNS'
                    audit_log.save()

            if len(txns) != 0:
                return Response({
                    'file': audit_log.file_name,
                    'id': audit_log.id,
                    'txns': len(txns)
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': "File did not meet conditions"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            audit_log.status = 'ERROR'
            audit_log.op_add_txt = str(e)
            audit_log.save()
            return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='all-txns', url_name='acct-all')
    def all_transactions(self, request: Request) -> Response:
        """
        Retrieve and filter all transactions for the authenticated user. This view provides support
        for search, filter, and ordering backends. Optionally, transactions can be filtered
        by associated file IDs.

        :param request: The incoming HTTP request containing any filtering and search criteria
            including optional `file_ids` in the request data for filtering transactions by files.

        :return: A paginated response with serialized transaction data or a full
            response containing all matched transactions if no pagination is applied.
        """
        queryset = Transaction.objects.filter(src_file__user=request.user)

        search_backend = SearchFilter()
        filter_backend = DjangoFilterBackend()
        ordering_backed = OrderingFilter()
        vs = TransactionViewSet()

        queryset = search_backend.filter_queryset(request, queryset, vs)
        queryset = filter_backend.filter_queryset(request, queryset, vs)
        queryset = ordering_backed.filter_queryset(request, queryset, vs)

        if request.data.get("file_ids", None):
            queryset = queryset.filter(src_file_id__in=request.data["file_ids"])

        queryset = queryset.select_related('src_file')
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='regroup')
    def rerun_grouper(self, request: Request, pk: int) -> Response:
        """
        Handles the operation to regroup transactions for a specific account, optionally
        filtering by specific files or blank groups.

        :param request: The HTTP request object containing user context and additional data
            for processing, including file identifiers and regrouping options.
        :param pk: The primary key of the account for which the regrouping operation should
            be applied.
        :return: A response object containing the count of transactions updated during the
            regrouping process or an error message in case of failure.
        """
        acc = self.get_object()
        files = FileAudit.objects.filter(op_desc='ACC_TXN_UPLOAD', user=request.user, to_id=acc.id)

        serializer = RerunGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.data.get('file_ids'):
            files = files.filter(id__in=request.data.get('file_ids'))

        queryset = Transaction.objects.filter(src_file__in=files)

        if serializer.validated_data['blanks_only']:
            queryset = queryset.filter(grp_name='')

        try:
            with transaction.atomic():
                txns = queryset.iterator(chunk_size=100)
                updated_txns = 0
                while True:
                    batch = []
                    try:
                        for _ in range(100):
                            txn = next(txns)
                            new_group = get_group(serializer.validated_data['grouper'], txn.txn_desc)
                            if new_group != txn.grp_name:
                                txn.grp_name = new_group
                                batch.append(txn)
                    except StopIteration:
                        if batch:
                            updated_txns += Transaction.objects.bulk_update(batch, ['grp_name'])
                        break
                    if batch:
                        updated_txns += Transaction.objects.bulk_update(batch, ['grp_name'])
                if updated_txns > 0:
                    for audit_file in files:
                        audit_file.op_add_txt = f"Regroup: {request.data['grouper']}"
                        audit_file.save()
            return Response({'updated_txns': updated_txns})
        except Exception as e:
            return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='delete-txn-files', url_name='acct-delete-by-files')
    def delete_file(self, request: Request, pk: int) -> Response:
        """
        Deletes transaction files associated with a specific account if matching file IDs are provided.

        This method processes the deletion of transaction files that are audited as part of the
        `ACC_TXN_UPLOAD` operation. It ensures transactional integrity during the deletion process
        to prevent partial updates and validates whether the specified file IDs exist before
        proceeding with deletion.

        :param request: The HTTP request object containing the necessary data for file deletion.
            It must include `file_ids` as part of the request payload to specify the files
            that should be deleted.
        :param pk: The primary key of the account object whose transaction files will be checked
            and deleted.
        :return: An HTTP response object indicating the status of the operation:
            - If `file_ids` are not specified, a 400 Bad Request response is returned
              with an appropriate error message.
            - If no files matching the provided IDs are found, a 404 Not Found response
              is returned with an error message.
            - On successful deletion, a 200 OK response is returned with the number of
              entries deleted and details of the deleted entries.
        """
        acc = self.get_object()

        if request.data.get("file_ids"):
            file_ids = request.data.get("file_ids")
        else:
            return Response({'error': "File IDs not specified"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = FileAudit.objects.filter(op_desc='ACC_TXN_UPLOAD', to_id=acc.id, pk__in=file_ids)

        if queryset.count() == 0:
            return Response({'error': "No transaction file found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            deleted_count, deleted_details = queryset.delete()

        return Response({
            "message": f"Successfully deleted {deleted_count} entries(s).",
            "details": deleted_details
        }, status=status.HTTP_200_OK)


class TransactionViewSet(RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = AccTransactionFilter
    search_fields = ['txn_desc', 'grp_name']
    ordering_fields = ['txn_date', 'txn_desc', 'grp_name', 'opr_dt', 'dbt_amount', 'cr_amount', 'cf_amt']

    def get_queryset(self):
        return Transaction.objects.filter(account__id=self.kwargs['acc_pk'],
                                          src_file__user=self.request.user).select_related('src_file', 'account')

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
