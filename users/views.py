from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid
from datetime import timedelta

from .serializers import (
    UserRegistrationSerializer,
    EmailVerificationSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    AddressSerializer
)
from .models import Address
from notifications.services import send_verification_email, send_password_reset_email

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """Vista para registro de usuario."""

    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Enviar email de verificación
        send_verification_email(user)

        return Response(
            {"detail": _("Registro exitoso. Por favor verifica tu correo electrónico.")},
            status=status.HTTP_201_CREATED
        )


class EmailVerificationView(APIView):
    """Vista para verificación de email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']

            try:
                user = User.objects.get(verification_token=token)

                # Verificar email
                user.email_verified = True
                user.verification_token = None
                user.verification_token_expires = None
                user.save()

                # Generar tokens de autenticación
                refresh = RefreshToken.for_user(user)

                return Response({
                    "detail": _("Email verificado correctamente."),
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response(
                    {"detail": _("Token inválido.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """Vista para inicio de sesión."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Vista para solicitar restablecimiento de contraseña."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Generar token de restablecimiento
            token = str(uuid.uuid4())
            user.password_reset_token = token
            user.password_reset_token_expires = timezone.now() + timedelta(hours=24)
            user.save()

            # Enviar email con instrucciones
            send_password_reset_email(user)

        except User.DoesNotExist:
            # No indicamos si el email existe o no por seguridad
            pass

        # Siempre devolvemos respuesta exitosa para no revelar si el email existe
        return Response(
            {"detail": _("Si tu email está registrado, recibirás instrucciones para restablecer tu contraseña.")},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """Vista para confirmar restablecimiento de contraseña."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        # Cambiar contraseña
        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires = None
        user.save()

        return Response(
            {"detail": _("Contraseña restablecida correctamente.")},
            status=status.HTTP_200_OK
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vista para ver y actualizar perfil de usuario."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear direcciones de entrega."""

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar direcciones de entrega."""

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)