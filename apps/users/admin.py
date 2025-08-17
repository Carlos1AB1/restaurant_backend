from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import VerificationToken

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # add_fieldsets se usa para el formulario de creación de usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'), # password2 no existe en el modelo, se maneja en el form
        }),
         ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    # readonly_fields = ('last_login', 'date_joined') # Ya están en BaseUserAdmin

# No necesitamos password2 aquí porque BaseUserAdmin ya maneja la creación
# Si no usaras BaseUserAdmin, necesitarías un UserCreationForm personalizado

class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'purpose', 'created_at', 'used')
    list_filter = ('purpose', 'used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('user', 'token', 'purpose', 'created_at')

admin.site.register(User, UserAdmin)
admin.site.register(VerificationToken, VerificationTokenAdmin)