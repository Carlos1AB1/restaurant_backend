from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo de Usuario."""

    def create_user(self, email, username, password=None, **extra_fields):
        """Crea y guarda un usuario con el email, username y contraseña."""
        if not email:
            raise ValueError(_('El usuario debe tener un email'))
        if not username:
            raise ValueError(_('El usuario debe tener un nombre de usuario'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Crea y guarda un superusuario con email, username y contraseña."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser debe tener is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo de usuario personalizado con email como identificador principal."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        _('dirección de correo'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        },
    )
    username = models.CharField(
        _('nombre de usuario'),
        max_length=150,
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este nombre de usuario."),
        },
    )
    first_name = models.CharField(_('nombre'), max_length=150, blank=True)
    last_name = models.CharField(_('apellido'), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Indica si el usuario puede acceder al sitio de administración.'),
    )
    is_active = models.BooleanField(
        _('activo'),
        default=True,
        help_text=_(
            'Indica si este usuario debe ser tratado como activo. '
            'Desmarcar esto en lugar de eliminar cuentas.'
        ),
    )
    date_joined = models.DateTimeField(_('fecha de registro'), default=timezone.now)

    # Campos adicionales para verificación de email
    email_verified = models.BooleanField(
        _('email verificado'),
        default=False,
        help_text=_('Indica si el usuario ha verificado su dirección de correo electrónico.'),
    )
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_expires = models.DateTimeField(blank=True, null=True)

    # Campo para reseteo de contraseña
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_expires = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Retorna el nombre corto del usuario."""
        return self.first_name


class Address(models.Model):
    """Modelo para direcciones de entrega de usuarios."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('usuario')
    )
    address_line1 = models.CharField(_('dirección línea 1'), max_length=255)
    address_line2 = models.CharField(_('dirección línea 2'), max_length=255, blank=True)
    city = models.CharField(_('ciudad'), max_length=100)
    state = models.CharField(_('estado/provincia'), max_length=100)
    postal_code = models.CharField(_('código postal'), max_length=20)
    country = models.CharField(_('país'), max_length=100)
    is_default = models.BooleanField(_('dirección predeterminada'), default=False)
    phone_number = models.CharField(_('número de teléfono'), max_length=20)

    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('dirección')
        verbose_name_plural = _('direcciones')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.postal_code}"

    def save(self, *args, **kwargs):
        # Si esta dirección se establece como predeterminada, desactivar las demás
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        # Si es la primera dirección del usuario, establecerla como predeterminada
        elif not Address.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)