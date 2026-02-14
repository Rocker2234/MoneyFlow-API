from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import FileAudit
from ..parsers import SUPPORTED_PARSERS


@api_view(['GET'])
@permission_classes([AllowAny])
def get_parsers(_request: Request) -> Response:
    return Response(SUPPORTED_PARSERS)


@api_view(['DELETE'])
def delete_uploaded_file(request: Request, file_id: int) -> Response:
    audit_file = get_object_or_404(FileAudit, pk=file_id, status='LOADED')

    if request.user != audit_file.user:
        return Response({"error": "Account does not belong to you!"}, status=status.HTTP_403_FORBIDDEN)

    audit_file.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
