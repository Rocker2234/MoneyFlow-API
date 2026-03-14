import os.path
import sys
import threading

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import UserSerializer, ChangePasswordSerializer, ResetPasswordSerializer


def del_reset_file(user):
    reset_file = os.path.join(settings.CONFIG_PATH, (user + '_reset.txt'))
    try:
        if os.path.exists(reset_file):
            os.remove(reset_file)
    except Exception as e:
        print("There was an error deleting the reset file:", file=sys.stderr)
        print(e, file=sys.stderr)


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


@api_view(['POST'])
def change_pw(request: Request) -> Response:
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save()

    response = Response(
        {"message": "Password updated successfully. Please login again."},
        status=status.HTTP_200_OK
    )

    response.delete_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
    )

    return response


@api_view(['POST'])
def reset_pw_file_create(request: Request) -> Response:
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reset_file = os.path.join(settings.CONFIG_PATH, (serializer.validated_data['user'] + '_reset.txt'))

    open(reset_file, 'w')

    response = Response(
        {
            "message": "File created successfully. Please check your config folder.",
            "user": request.data['user'],
            "path": reset_file
        },
        status=status.HTTP_200_OK
    )

    t = threading.Timer(int(settings.USER_SETTINGS.get("Main", 'pw_reset_file_timeout')), del_reset_file,
                        (serializer.validated_data['user'],))
    t.daemon = True
    t.start()

    return response


@api_view(['POST'])
def reset_pw(request: Request) -> Response:
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reset_file = os.path.join(settings.CONFIG_PATH, (serializer.validated_data['user'] + '_reset.txt'))

    try:
        with open(reset_file, 'r') as f:
            pw = f.readline().strip()
        if not pw:
            return Response({"message": "Please enter new password on the file!"}, status=status.HTTP_400_BAD_REQUEST)
        os.remove(reset_file)
    except FileNotFoundError:
        return Response({"message": "There was no request made to reset password for this user."},
                        status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.get(username=serializer.validated_data['user'])
    user.set_password(pw)
    user.save()

    return Response(
        {"message": "Password updated successfully."},
        status=status.HTTP_200_OK
    )


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
