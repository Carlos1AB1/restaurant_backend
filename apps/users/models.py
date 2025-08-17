from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

from .managers import CustomUserManager  # Importa el manager personalizado


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)

    # Nueva línea para añadir el campo is_deliverer
    is_deliverer = models.BooleanField(default=False, verbose_name=_('Is Deliverer'))

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # Inactivo hasta verificar email
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Campos requeridos al crear superuser

    objects = CustomUserManager()  # Usa el manager personalizado

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


# Modelo para almacenar tokens de verificación/reseteo (alternativa simple a JWT para esto)
class VerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, choices=[('VERIFY', 'Email Verification'), ('RESET', 'Password Reset')])

    def is_valid(self):
        # Define un tiempo de expiración, por ejemplo, 1 día
        return not self.used and (timezone.now() - self.created_at) < timedelta(days=1)