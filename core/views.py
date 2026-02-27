from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
def logout_user(request: Request) -> Response:
    """
    Handles user logout by deleting the authentication cookie and returning a success response.

    :param request: The HTTP request object representing the incoming request to log out a user.
    :return: A response object containing a success message indicating the user has been
             successfully logged out.
    """
    response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    response.delete_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    )
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request: Request) -> Response:
    """
    Registers a new user and returns authentication tokens along with the username.
    The access token is included in the response body, while the refresh token is
    stored in a cookie.

    :param request:
        The HTTP request object containing the user's registration data. This should
        include "username", "password" and "home_currency".

    :return:
        A Django Rest Framework Response object with the following:
            - access: The generated access token for authenticating later requests.
            - user: The username of the newly registered user.
        Additionally, a secure, HTTP-only cookie is set with the refresh token.
    """
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    responce = Response({
        'access': str(refresh.access_token),
        'user': serializer.data,
    }, status=status.HTTP_201_CREATED)

    responce.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=str(refresh),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
    )

    return responce


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')

        # Set the cookie
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=refresh_token,
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        )

        # Remove the refresh token from the JSON body for security
        response.data.pop('refresh')
        response.data['user'] = request.data.get('username')

        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs):
        # Extract the refresh token from the cookie
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if refresh_token:
            request.data['refresh'] = refresh_token

        return super().post(request, *args, **kwargs)
