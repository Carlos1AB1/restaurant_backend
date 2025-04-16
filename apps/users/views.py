from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import VerificationToken
from .utils import send_verification_email, send_password_reset_email
from rest_framework.permissions import AllowAny, IsAuthenticated

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] # Cualquiera puede registrarse

    def perform_create(self, serializer):
        user = serializer.save()
        # Crear token de verificación
        token = VerificationToken.objects.create(user=user, purpose='VERIFY')
        # Enviar email (maneja el fallo si ocurre)
        send_verification_email(user, token)


# apps/users/views.py - Modificar la clase VerifyEmailView

class VerifyEmailView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        try:
            # Busca el token válido (no usado y no expirado - lógica en el modelo)
            verification_token = VerificationToken.objects.get(token=token, purpose='VERIFY')

            if verification_token.used:
                # El token ya ha sido utilizado, pero es válido
                # Cambio del mensaje para diferenciar este caso
                return Response({
                    "message": "Esta cuenta ya está activa.",
                    "status": "already_verified"
                }, status=status.HTTP_200_OK)

            # Simplificamos: asumimos validez si se encuentra y no está usado.
            # if not verification_token.is_valid(): # Si implementas is_valid() con tiempo
            #    return Response({"error": "El token es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

            user = verification_token.user
            if user.is_active:
                # El usuario ya está activo, pero el token no se ha marcado como usado
                verification_token.used = True
                verification_token.save()
                return Response({
                    "message": "Esta cuenta ya está activa.",
                    "status": "already_verified"
                }, status=status.HTTP_200_OK)

            # Caso principal: activar la cuenta por primera vez
            user.is_active = True
            user.save()
            verification_token.used = True
            verification_token.save()

            return Response({
                "message": "Cuenta verificada exitosamente. Ahora puedes iniciar sesión.",
                "status": "verified"
            }, status=status.HTTP_200_OK)

        except VerificationToken.DoesNotExist:
            return Response({"error": "Token de verificación inválido."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error en VerifyEmailView: {e}")
            return Response({"error": "Ocurrió un error durante la verificación."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Usaremos las vistas de SimpleJWT para login y refresh
class CustomTokenObtainPairView(TokenObtainPairView):
    # Puedes personalizar el serializer aquí si necesitas añadir más datos al token
    # serializer_class = MyTokenObtainPairSerializer
    pass

class CustomTokenRefreshView(TokenRefreshView):
    pass


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Invalida tokens de reseteo anteriores para este usuario
            VerificationToken.objects.filter(user=user, purpose='RESET', used=False).update(used=True)
            # Crea un nuevo token
            token = VerificationToken.objects.create(user=user, purpose='RESET')
            # Envía el email
            send_password_reset_email(user, token)
            return Response({"message": "Se ha enviado un enlace de restablecimiento de contraseña a tu correo."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
             # La validación del serializer ya cubre esto, pero por si acaso
             return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error en PasswordResetRequestView: {e}")
            return Response({"error": "No se pudo procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        try:
            reset_token = VerificationToken.objects.get(token=token, purpose='RESET')

            if reset_token.used:
                 return Response({"error": "Este token ya ha sido utilizado."}, status=status.HTTP_400_BAD_REQUEST)

            # Opcional: verificar expiración si implementaste is_valid() con tiempo
            # if not reset_token.is_valid():
            #     return Response({"error": "El token es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

            user = reset_token.user
            user.set_password(password)
            user.save()

            reset_token.used = True
            reset_token.save()

            return Response({"message": "Contraseña restablecida exitosamente."}, status=status.HTTP_200_OK)

        except VerificationToken.DoesNotExist:
            return Response({"error": "Token inválido."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error en PasswordResetConfirmView: {e}")
            return Response({"error": "Ocurrió un error al restablecer la contraseña."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vista para ver y actualizar el perfil del usuario autenticado.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Devuelve el usuario asociado a la solicitud actual
        return self.request.user

    # El método update ya está implementado por RetrieveUpdateAPIView
    # Se podrían añadir validaciones específicas si fuera necesario en perform_update