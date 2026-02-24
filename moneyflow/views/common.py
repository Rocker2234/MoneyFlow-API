import json

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..filters import AuditFileFilter
from ..models import FileAudit
from ..pagination import DefaultPagination
from ..parsers import SUPPORTED_PARSERS
from ..serializers.common_serializers import FileAuditSerializer


class FileAuditViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
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

    def partial_update(self, request, *args, **kwargs) -> Response:
        return Response({"detail": "Method \"PATCH\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs) -> Response:
        return Response({"detail": "Method \"PUT\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['patch'], url_path='note')
    def add_message(self, request: Request, pk: int) -> Response:
        """
        Add a user message to the file audit object. The custom message is
        stored in JSON format within the `op_add_txt` field.

        :param request: The HTTP request containing the data to update the
            `op_add_txt` field. Expected to include a `message` key in the request
            data.
        :param pk: The primary key of the `FileAudit` object to update.
        :return: A Response object containing the request data after updating the
            `FileAudit` object.
        """
        audit_file: FileAudit = self.get_queryset().get(pk=pk)
        message = request.data.get('message', '')
        op_add_txt: dict = json.loads(audit_file.op_add_txt if audit_file.op_add_txt else "{}")
        op_add_txt['user_message'] = message
        audit_file.op_add_txt = json.dumps(op_add_txt)
        audit_file.save()

        return Response(request.data)


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
