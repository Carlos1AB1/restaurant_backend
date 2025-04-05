import os
from celery import Celery
from django.conf import settings

# Establecer variable de entorno para configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_api.settings')

# Crear instancia de Celery
app = Celery('restaurant_api')

# Cargar configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir tareas automáticamente
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    """
    Tarea de depuración para probar Celery.
    """
    print(f'Request: {self.request!r}')