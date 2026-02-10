from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template import TemplateDoesNotExist
from django.utils import timezone
from jinja2 import FileSystemLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .file_actions import get_reader, get_group
from .models import Account, Transaction, FileAudit
from .parsers import SUPPORTED_PARSERS
from .serializers import AccountSerializer, TransactionSerializer


@api_view()
def check_conn(_request: Request) -> Response:
    return Response("OK")


@api_view(['POST'])
def add_account(request: Request) -> Response:
    serializer = AccountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE', 'PATCH'])
def account(request: Request, acc_id: int) -> Response | None:
    acc = get_object_or_404(Account, pk=acc_id)

    if request.method == 'GET':
        serializer = AccountSerializer(acc)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AccountSerializer(acc, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    elif request.method == 'DELETE':
        if acc.transactions.count() > 0:
            return Response({'error': 'Account is accosiated with transactions!'}, status=status.HTTP_400_BAD_REQUEST)
        acc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == 'PATCH':
        serializer = AccountSerializer(acc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    return None


@api_view(['GET'])
def get_parsers(_request: Request) -> Response:
    return Response(SUPPORTED_PARSERS)


@api_view(['PATCH'])
def edit_account(request: Request, acc_id: int) -> Response:
    txn = get_object_or_404(Transaction, pk=acc_id)
    allowed_fields = {'def_grouper'}
    if not set(request.data.keys()).issubset(allowed_fields):
        return Response({'error': f'Only support {allowed_fields}'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TransactionSerializer(txn, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
def add_transaction(request: Request) -> Response:
    serializer = TransactionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def upload_transaction_file(request: Request) -> Response:
    try:
        acc = get_object_or_404(Account, pk=request.data['account'])
        dt_format = request.data['dt_format']
        parser = request.data['parser']
        grouper = request.data['grouper']
        if (parser not in SUPPORTED_PARSERS.keys()) or parser == "NULL":
            return Response({'error': 'Parser {} is not supported'.format(parser)}, status=status.HTTP_400_BAD_REQUEST)
    except KeyError as e:
        return Response({'error': f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES.get('file')
    if uploaded_file is None:
        return Response({'error': 'No file provided!'}, status=status.HTTP_400_BAD_REQUEST)

    txns = []

    audit_log = FileAudit.objects.create(
        file_name=uploaded_file.name,
        to_id=acc.id,
        op_desc='TXN_UPLOAD',
        status='LOADING',
        op_args=f'Acc:{acc.id}, dt_format:{dt_format}, reader:{parser}, grouper:{grouper}',
    )

    try:
        reader = get_reader(uploaded_file, parser)
        with transaction.atomic():
            template = None
            if grouper not in (None, "", "NULL"):
                template = SandboxedEnvironment(
                    loader=FileSystemLoader(settings.USER_SETTINGS.get("Main", "templates"))).get_template(
                        'G_' + grouper + '.j2')
            for row in reader:
                txns.append(Transaction(
                    account=acc,
                    txn_date=datetime.strptime(row['txn_date'], dt_format).date().isoformat(),
                    txn_desc=row['txn_desc'],
                    grp_name=get_group(template, row['txn_desc']),
                    opr_dt=timezone.make_aware(datetime.strptime(row['opr_dt'], dt_format)),
                    dbt_amount=row['dbt_amount'],
                    cr_amount=row['cr_amount'],
                    ref_num=row['ref_num'],
                    cf_amt=row['cf_amt'],
                    src_file=audit_log
                ))
            Transaction.objects.bulk_create(txns)
            audit_log.status = 'LOADED'
            audit_log.save()
        return Response({
            'file': audit_log.file_name,
            'id': audit_log.id,
        }, status=status.HTTP_201_CREATED)
    except TemplateDoesNotExist as e:
        audit_log.status = 'FAILED'
        audit_log.op_add_txt = f"{e.__class__.__name__}: {e}"
        audit_log.save()
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        audit_log.status = 'ERROR'
        audit_log.op_add_txt = str(e)
        audit_log.save()
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
def edit_transaction(request: Request, txn_id: int) -> Response:
    txn = get_object_or_404(Transaction, pk=txn_id)
    allowed_fields = {'grp_name'}
    if not set(request.data.keys()).issubset(allowed_fields):
        return Response({'error': f'Only support {allowed_fields}'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TransactionSerializer(txn, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['PATCH'])
def rerun_grouper(request: Request, file_id: int) -> Response:
    try:
        grouper = request.data['grouper']
        blanks_only = request.data['blanks_only']
        template = None
        if grouper not in (None, "", "NULL"):
            template = SandboxedEnvironment(
                loader=FileSystemLoader(settings.USER_SETTINGS.get("Main", "templates"))).get_template(
                'G_' + grouper + '.j2')
    except KeyError as e:
        return Response({'error': f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except TemplateNotFound as e:
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = get_object_or_404(FileAudit, pk=file_id)
    query_set = Transaction.objects.filter(src_file=uploaded_file)

    if blanks_only:
        query_set = query_set.filter(grp_name='')

    try:
        with transaction.atomic():
            txns = query_set.iterator(chunk_size=100)
            updated_txns = 0
            while True:
                batch = []
                try:
                    for _ in range(100):
                        txn = next(txns)
                        new_group = get_group(template, txn.txn_desc)
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
                uploaded_file.op_add_txt = f"Regroup: {grouper}"
                uploaded_file.save()
        return Response({'updated_txns': updated_txns})
    except Exception as e:
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_transactions(request: Request) -> Response:
    try:
        file_ids = request.data['file_ids']
    except KeyError as e:
        return Response({'error': f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    queryset = Transaction.objects.filter(src_file_id__in=file_ids)
    serializer = TransactionSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_uploaded_file(_request: Request, file_id: int) -> Response:
    audit_file = get_object_or_404(FileAudit, pk=file_id)
    audit_file.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
