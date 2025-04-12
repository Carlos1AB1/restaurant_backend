# restaurant_backend/restaurant_backend/wsgi.py

"""
WSGI config for restaurant_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Esta línea es crucial: asegura que Django sepa dónde encontrar settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_backend.settings')

# Esta línea crea el objeto 'application' que el servidor WSGI busca.
application = get_wsgi_application()