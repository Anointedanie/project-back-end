"""
URL routes for user authentication endpoints.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    ChangePasswordView,
    AdminUserListView,
)

urlpatterns = [
    # Authentication endpoints
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', UserLoginView.as_view(), name='login'),
    path('logout', UserLogoutView.as_view(), name='logout'),

    # Token refresh endpoint
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # User profile endpoints
    path('profile', UserProfileView.as_view(), name='profile'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),

    # Admin endpoints
    path('users', AdminUserListView.as_view(), name='user_list'),
]
