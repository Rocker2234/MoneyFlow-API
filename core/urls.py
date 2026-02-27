from django.urls import path

from . import views

urlpatterns = [
    # TEST Connection
    path('test/', views.check_conn, name='test_connection'),
    path('register/', views.register_user, name='register'),
    path('login/', views.CookieTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout_user, name='logout'),
]
