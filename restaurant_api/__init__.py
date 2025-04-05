from __future__ import absolute_import, unicode_literals

# Importar configuración de Celery para cargarla cuando Django inicia
from .celery import app as celery_app

__all__ = ('celery_app',)