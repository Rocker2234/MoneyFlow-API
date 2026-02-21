from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def check_conn(_request: Request) -> Response:
    """
    Provides an endpoint to check server connection health. This utility function
    returns a simple success message to confirm that the service is running and
    accessible.
    """
    return Response("OK")


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request: Request) -> Response:
    """
    Registers a new user and returns JWT authentication tokens and user details. This view
    handles user registration by validating the provided data and creating a new user
    if the data is valid. Upon successful registration, it returns the access and refresh
    tokens for authentication, along with the user's serialized data.

    :param request: An HTTP request object containing the registration data in its body.

    :return: A Response object containing the access and refresh tokens, and the user's
        serialized data upon successful registration. The response has an HTTP status
        code of 201 (Created).
    """
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': serializer.data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request: Request) -> Response:
    """
    Authenticates a user based on provided credentials in the request data and returns
    access and refresh tokens if successful. If the user is not found or credentials
    are invalid, it returns an error message with Unauthorized status.

    :param request: A Request object containing 'username' and 'password'.

    :return: Response containing access token, refresh token, and username if
             authentication is successful, otherwise an error message with HTTP
             401 Unauthorized status.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user.get_username()
            })
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
