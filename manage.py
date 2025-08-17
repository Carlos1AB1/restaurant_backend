# restaurant_backend/manage.py

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def main():
    """Run administrative tasks."""
    # Establece la variable de entorno 'DJANGO_SETTINGS_MODULE'.
    # Le dice a Django dónde encontrar tu archivo settings.py.
    # Ajusta 'restaurant_backend.settings' si tu directorio de configuración
    # tiene un nombre diferente o si moviste settings.py.
    # En tu estructura, 'restaurant_backend' es el directorio que contiene settings.py.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_backend.settings')

    # Añadir el directorio padre (que contiene la carpeta 'apps') al sys.path
    # Esto asegura que las importaciones como 'from apps.users...' funcionen
    # al ejecutar comandos de manage.py.
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.append(str(BASE_DIR))
    # También podríamos añadir directamente la carpeta 'apps' si fuera necesario,
    # aunque añadir el directorio base suele ser suficiente si las apps
    # se importan como 'apps.nombre_app'.
    # sys.path.append(str(BASE_DIR / 'apps'))


    try:
        # Intenta importar la función execute_from_command_line de Django.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Si Django no está instalado o no se encuentra en el PYTHONPATH,
        # lanza un error informativo.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Ejecuta el comando de Django que se pasó a manage.py
    # (ej: runserver, migrate, createsuperuser, etc.)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Este bloque asegura que la función main() se ejecute solo
    # cuando el script es llamado directamente.
    main()