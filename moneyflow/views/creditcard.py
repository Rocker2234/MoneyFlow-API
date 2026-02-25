import json
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
from ..filters import CreditTransactionFilter, CreditSearchFilter
from ..models import FileAudit
from ..pagination import DefaultPagination
from ..serializers.creditcard_serializers import *


class CreditCardViewSet(ModelViewSet):
    serializer_class = CreditCardSerializer
    pagination_class = DefaultPagination

    filter_backends = [CreditSearchFilter]
    filterset_class = CreditTransactionFilter
    ordering_fields = ['txn_date', 'grp_name', 'amt', 'is_credit']

    def get_queryset(self) -> QuerySet:
        return CreditCard.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        if CreditTransaction.objects.filter(credit_card__id=kwargs['pk']).select_related('credit_card').count() > 0:
            return Response({'error': 'Card is accosiated with transactions!'}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='all-txns', url_name='cct-all')
    def all_transactions(self, request: Request) -> Response:
        """
        Handles the retrieval of all credit transactions associated with the authenticated user. The method
        applies search, filtering, and ordering to the transactions based on the provided request parameters.
        It retrieves user-specific transactions, optionally filters them by file IDs, and prepares the
        resulting queryset for paginated or non-paginated response in case of problems with pagination.

        :param request: The HTTP request object containing user authentication, filters, and optional file IDs.
        :return: A paginated or complete response containing serialized transaction data matching the user's
                 query and filters.
        """
        queryset = CreditTransaction.objects.filter(src_file__user=request.user).order_by('-txn_date', '-id')

        search_backend = CreditSearchFilter()
        filter_backend = DjangoFilterBackend()
        ordering_backed = OrderingFilter()

        queryset = search_backend.filter_queryset(request, queryset, self)
        queryset = filter_backend.filter_queryset(request, queryset, self)
        queryset = ordering_backed.filter_queryset(request, queryset, self)

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

    @action(detail=True, methods=['post'], url_path='upload')
    def upload_transaction_file(self, request: Request, pk: int) -> Response:
        """
        Handles the uploading of transaction files for a specific credit card account. This method
        parses the uploaded file, validates the content, and processes transaction data to persist
        it into the database. In addition, it logs the operation audit, including file details and
        status updates.

        :param request: The HTTP request object containing the uploaded file and additional
            parameters for file processing, such as date format and parser choice.

        :param pk: The primary key identifying the credit card account to which transactions
            relate.

        :return: Response containing details of the file upload upon successful processing,
            or an error message in case of exceptions.
        """
        cc = self.get_object()

        serializer = TransactionFileUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        dt_format = serializer.validated_data['dt_format']
        parser = serializer.validated_data['parser']

        uploaded_file = request.FILES.get('file')

        txns = []
        op_json = {"dt_format": dt_format, "parser": parser}

        if serializer.validated_data["grouper"]:
            op_json["grouper"] = serializer.validated_data["grouper"].name[2:-3]
        else:
            op_json["grouper"] = None

        op_json = json.dumps(op_json)

        audit_log = FileAudit.objects.create(
            file_name=uploaded_file.name,
            to_id=cc.id,
            op_desc='CC_TXN_UPLOAD',
            status='LOADING',
            op_args=op_json,
            user=request.user
        )

        try:
            reader = get_reader(uploaded_file, parser)
            with transaction.atomic():
                for row in reader:
                    txns.append(CreditTransaction(
                        credit_card=cc,
                        txn_date=timezone.make_aware(datetime.strptime(row['txn_date'], dt_format),
                                                     ZoneInfo(settings.USER_SETTINGS.get("Main", "home_tz"))),
                        txn_desc=row['txn_desc'],
                        grp_name=get_group(serializer.validated_data['grouper'], row['txn_desc']),
                        amt=row['amt'],
                        is_credit=row['is_credit'] == 'Y',
                        src_file=audit_log
                    ))
                CreditTransaction.objects.bulk_create(txns)
                audit_log.status = 'LOADED'
                audit_log.save()
            return Response({
                'file': audit_log.file_name,
                'id': audit_log.id,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            audit_log.status = 'ERROR'
            audit_log.op_add_txt = json.dumps({'error': f"{e.__class__.__name__}: {e}"})
            audit_log.save()
            return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            audit_log.status = 'ERROR'
            audit_log.op_add_txt = json.dumps({'error': f"{e.__class__.__name__}: {e}"})
            audit_log.save()
            return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='delete-txn-files', url_name='cct-delete-by-files')
    def delete_file(self, request: Request, pk: int) -> Response:
        """
        Handles the deletion of specific transaction files related to a given object.

        The method retrieves the associated object and deletes the specified files
        based on their IDs. The operation is atomic, ensuring that the database state
        is not partially updated if an error occurs during execution.

        :param request: The HTTP request containing the file IDs to delete in the payload.
        :param pk: The primary key of the credit card to which the transaction files are tied.
        :return: A Response containing the deletion status and details of the deleted files,
            or an error message with the respective status code.
        """
        cc = self.get_object()

        if request.data.get("file_ids", None):
            file_ids = request.data.get("file_ids")
        else:
            return Response({'error': "File IDs not specified"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            queryset = FileAudit.objects.filter(op_desc='CC_TXN_UPLOAD', to_id=cc.id, pk__in=file_ids)

            if queryset.count() == 0:
                return Response({'error': "File not found"}, status=status.HTTP_404_NOT_FOUND)

            deleted_count, deleted_details = queryset.delete()
            return Response({
                "message": f"Successfully deleted {deleted_count} entries(s).",
                "details": deleted_details
            }, status=status.HTTP_200_OK)


class TransactionViewSet(RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPagination

    filterset_class = CreditTransactionFilter
    search_fields = ['txn_desc', 'grp_name']
    ordering_fields = ['txn_date', 'grp_name', 'amt', 'is_credit']

    def get_queryset(self):
        return CreditTransaction.objects.filter(credit_card__id=self.kwargs['cc_pk'],
                                                src_file__user=self.request.user
                                                ).select_related('src_file', 'credit_card').order_by('-txn_date', 'id')
