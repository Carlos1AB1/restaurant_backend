from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView,
    EmailVerificationView,
    UserLoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfileView,
    AddressListCreateView,
    AddressDetailView
)

urlpatterns = [
    # Autenticación
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Recuperación de contraseña
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Perfil de usuario
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Direcciones
    path('addresses/', AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<uuid:pk>/', AddressDetailView.as_view(), name='address-detail'),
]