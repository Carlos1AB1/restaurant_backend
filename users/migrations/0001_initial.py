# Generated by Django 5.1.7 on 2025-04-05 03:42

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(error_messages={'unique': 'Ya existe un usuario con este correo electrónico.'}, max_length=254, unique=True, verbose_name='dirección de correo')),
                ('username', models.CharField(error_messages={'unique': 'Ya existe un usuario con este nombre de usuario.'}, max_length=150, unique=True, verbose_name='nombre de usuario')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='nombre')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='apellido')),
                ('is_staff', models.BooleanField(default=False, help_text='Indica si el usuario puede acceder al sitio de administración.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Indica si este usuario debe ser tratado como activo. Desmarcar esto en lugar de eliminar cuentas.', verbose_name='activo')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='fecha de registro')),
                ('email_verified', models.BooleanField(default=False, help_text='Indica si el usuario ha verificado su dirección de correo electrónico.', verbose_name='email verificado')),
                ('verification_token', models.CharField(blank=True, max_length=100, null=True)),
                ('verification_token_expires', models.DateTimeField(blank=True, null=True)),
                ('password_reset_token', models.CharField(blank=True, max_length=100, null=True)),
                ('password_reset_token_expires', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'usuario',
                'verbose_name_plural': 'usuarios',
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('address_line1', models.CharField(max_length=255, verbose_name='dirección línea 1')),
                ('address_line2', models.CharField(blank=True, max_length=255, verbose_name='dirección línea 2')),
                ('city', models.CharField(max_length=100, verbose_name='ciudad')),
                ('state', models.CharField(max_length=100, verbose_name='estado/provincia')),
                ('postal_code', models.CharField(max_length=20, verbose_name='código postal')),
                ('country', models.CharField(max_length=100, verbose_name='país')),
                ('is_default', models.BooleanField(default=False, verbose_name='dirección predeterminada')),
                ('phone_number', models.CharField(max_length=20, verbose_name='número de teléfono')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='actualizado el')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'dirección',
                'verbose_name_plural': 'direcciones',
                'ordering': ['-is_default', '-created_at'],
            },
        ),
    ]
