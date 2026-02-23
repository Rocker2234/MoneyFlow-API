from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..filters import AuditFileFilter
from ..models import FileAudit
from ..pagination import DefaultPagination
from ..parsers import SUPPORTED_PARSERS
from ..serializers.common_serializers import FileAuditSerializer


class FileAuditViewSet(ListModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = FileAuditSerializer
    pagination_class = DefaultPagination

    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['file_name']
    filterset_class = AuditFileFilter

    def get_queryset(self):
        queryset = FileAudit.objects.filter(user=self.request.user)
        if self.request.data.get("op_desc"):
            queryset = queryset.filter(op_desc=self.request.data["op_desc"])
            if self.request.data.get("acc_id"):
                queryset = queryset.filter(to_id=self.request.data["acc_id"])
        return queryset.order_by('-isrt_dt', 'id')

    def get_serializer_context(self):
        return {'request': self.request}


@api_view(['GET'])
@permission_classes([AllowAny])
def get_parsers(_request: Request) -> Response:
    """
    This function is exposed as an API endpoint to return a list of parsers
    supported by the application.

    :param _request: The incoming HTTP request from the client.
    :return: A response object containing the list of supported parsers.
    """
    return Response(SUPPORTED_PARSERS)
