from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from ..parsers import SUPPORTED_PARSERS


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
