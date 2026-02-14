from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from ..file_actions import get_reader, get_group
from ..models import FileAudit
from ..serializers.creditcard_serializers import *


@api_view(['POST'])
def add_card(request: Request) -> Response:
    serializer = CreditCardSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def credit_card(request: Request, cc_id: int) -> Response:
    cc = CreditCard.objects.get(pk=cc_id)

    if request.user != cc.user:
        return Response({"error": "Account does not belong to you!"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = CreditCardSerializer(cc)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = CreditCardSerializer(cc, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = CreditCardSerializer(cc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    elif request.method == 'DELETE':
        if cc.credit_transactions.count() > 0:
            return Response({'error': 'Card is accosiated with transactions!'}, status=status.HTTP_400_BAD_REQUEST)
        cc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def upload_transaction_file(request: Request) -> Response:
    serializer = TransactionFileUploadSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    cc = serializer.validated_data['credit_card']
    dt_format = serializer.validated_data['dt_format']
    parser = serializer.validated_data['parser']

    uploaded_file = request.FILES.get('file')
    # if uploaded_file is None:
    #     return Response({'error': 'No file provided!'}, status=status.HTTP_400_BAD_REQUEST)

    txns = []

    audit_log = FileAudit.objects.create(
        file_name=uploaded_file.name,
        to_id=cc.id,
        op_desc='CC_TXN_UPLOAD',
        status='LOADING',
        op_args=f'CC:{cc.id}, dt_format:{dt_format}, reader:{parser}, grouper:{request.data.get("grouper", "")}',
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
        audit_log.op_add_txt = str(e)
        audit_log.save()
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        audit_log.status = 'ERROR'
        audit_log.op_add_txt = str(e)
        audit_log.save()
        return Response({'error': f"{e.__class__.__name__}: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
def edit_transaction(request: Request, txn_id: int) -> Response:
    txn = get_object_or_404(CreditTransaction, pk=txn_id)

    if request.user != txn.credit_card.user:
        return Response({"error": "Transaction does not belong to you!"}, status=status.HTTP_403_FORBIDDEN)

    allowed_fields = {'grp_name'}
    if not set(request.data.keys()).issubset(allowed_fields):
        return Response({'error': f'Only support {allowed_fields}'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TransactionSerializer(txn, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET'])
def get_transactions_by_file(request: Request) -> Response:
    try:
        file_ids = request.data['file_ids']
    except KeyError as e:
        return Response({'error': f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    queryset = CreditTransaction.objects.filter(src_file_id__in=file_ids, src_file__user=request.user,
                                                src_file__op_desc='CC_TXN_UPLOAD').select_related('src_file')
    serializer = TransactionSerializer(queryset, many=True)
    return Response(serializer.data)
