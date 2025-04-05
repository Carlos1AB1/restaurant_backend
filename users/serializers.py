from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid
from .models import Address

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para el registro de usuarios."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        # Validar que las contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Las contraseñas no coinciden.")})
        return attrs

    def create(self, validated_data):
        # Eliminar password_confirm del diccionario
        validated_data.pop('password_confirm')

        # Generar token de verificación
        verification_token = str(uuid.uuid4())
        verification_token_expires = timezone.now() + timedelta(days=1)

        # Crear usuario
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            verification_token=verification_token,
            verification_token_expires=verification_token_expires,
            is_active=True,  # Usuario activo pero sin email verificado
            email_verified=False
        )

        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer para verificación de email."""

    token = serializers.CharField(required=True)

    def validate_token(self, value):
        try:
            user = User.objects.get(verification_token=value)

            # Verificar que el token no haya expirado
            if user.verification_token_expires < timezone.now():
                raise serializers.ValidationError(_("El token de verificación ha expirado."))

            # Verificar que el email no esté ya verificado
            if user.email_verified:
                raise serializers.ValidationError(_("Este email ya ha sido verificado."))

            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Token de verificación inválido."))


class UserLoginSerializer(serializers.Serializer):
    """Serializer para inicio de sesión de usuario."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Autenticar usuario
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )

            if not user:
                msg = _('No se pudo iniciar sesión con las credenciales proporcionadas.')
                raise serializers.ValidationError(msg, code='authorization')

            # Verificar que el usuario esté activo
            if not user.is_active:
                raise serializers.ValidationError(_('La cuenta de usuario está desactivada.'))

            # Verificar que el email esté verificado
            if not user.email_verified:
                raise serializers.ValidationError(_('El email de usuario no ha sido verificado.'))

            attrs['user'] = user
            return attrs
        else:
            msg = _('Debe incluir "email" y "password".')
            raise serializers.ValidationError(msg, code='authorization')


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitud de restablecimiento de contraseña."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError(_("Esta cuenta de usuario está desactivada."))
            return value
        except User.DoesNotExist:
            # Por seguridad, no indicamos si el email existe o no
            return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar restablecimiento de contraseña."""

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        # Validar que las contraseñas coincidan
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Las contraseñas no coinciden.")})

        # Validar el token
        try:
            user = User.objects.get(password_reset_token=attrs['token'])

            # Verificar que el token no haya expirado
            if user.password_reset_token_expires < timezone.now():
                raise serializers.ValidationError({"token": _("El token ha expirado.")})

            attrs['user'] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({"token": _("Token inválido.")})


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario."""

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'date_joined', 'email_verified']
        read_only_fields = ['id', 'email', 'date_joined', 'email_verified']


class AddressSerializer(serializers.ModelSerializer):
    """Serializer para direcciones de entrega."""

    class Meta:
        model = Address
        fields = [
            'id', 'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'is_default', 'phone_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Asignar el usuario actual a la dirección
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)