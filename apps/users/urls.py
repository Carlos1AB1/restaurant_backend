from django.urls import path
from .views import (
    UserRegistrationView,
    VerifyEmailView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfileView,
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'), # El frontend llamará a esta API
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'), # El frontend llamará a esta API
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]