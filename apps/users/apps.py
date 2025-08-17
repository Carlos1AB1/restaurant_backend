# restaurant_backend/apps/users/apps.py

from django.apps import AppConfig

class UsersConfig(AppConfig):
    """
    Configuración de la aplicación de Usuarios.

    Define el tipo de campo AutoField por defecto y el nombre
    interno y legible de la aplicación.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    # El nombre debe coincidir con la ruta del directorio desde la raíz del proyecto
    # (o desde donde Django busca las apps, en este caso dentro de 'apps')
    name = 'apps.users'
    # Nombre legible que aparecerá en el panel de administración de Django
    verbose_name = "Gestión de Usuarios"

    # No se necesita la función ready() aquí porque no estamos conectando
    # señales directamente en este archivo para la app 'users'.
    # Las señales para otros modelos (como Order) se conectan en sus respectivas
    # apps.py o usando decoradores @receiver.
    # def ready(self):
    #     import apps.users.signals # Solo si tuvieras señales específicas de usuario aquí