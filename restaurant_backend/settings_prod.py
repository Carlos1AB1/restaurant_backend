# Configuración para producción
import os
from .settings import *
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.prod
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.prod'))

# Seguridad
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Permitir DEBUG desde .env
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Configuración CSRF específica para producción (usar variables de entorno)
# IMPORTANTE: Django exige esquema (http/https) en cada origen.
# Ejemplo de variable: CSRF_TRUSTED_ORIGINS="https://api.mi-dominio.com,https://mi-elb.amazonaws.com"
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o]

# Configuración de cookies para CSRF y sesión
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_AGE = 31449600
CSRF_COOKIE_DOMAIN = None

# Cookies "secure" solo si no estamos en DEBUG (HTTPS en prod)
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'

# Email y contacto
RESTAURANT_CONTACT_EMAIL = os.getenv('RESTAURANT_CONTACT_EMAIL', 'admin@restaurant.com')

# Base de datos para producción (RDS)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('AWS_DB_NAME'),
        'USER': os.getenv('AWS_DB_USER'),
        'PASSWORD': os.getenv('AWS_DB_PASSWORD'),
        'HOST': os.getenv('AWS_DB_HOST'),
        'PORT': os.getenv('AWS_DB_PORT', '5432'),
    }
}

# Configuración de archivos estáticos para desarrollo (local)
# Comentar la configuración S3 temporalmente para que Swagger funcione
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Configuración de archivos estáticos locales
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Deshabilitamos S3 temporalmente
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'

# Configuración de seguridad
SECURE_SSL_REDIRECT = False  # Deshabilitado para testing - habilitar cuando tengas HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Headers de seguridad adicionales
SECURE_CROSS_ORIGIN_OPENER_POLICY = None  # Deshabilitar para evitar advertencias en HTTP

# Configuración CORS para producción
CORS_ALLOW_ALL_ORIGINS = True  # Cambia a False cuando definas dominios exactos
CORS_ALLOW_CREDENTIALS = True
# Si deshabilitas CORS_ALLOW_ALL_ORIGINS, configura CORS_ALLOWED_ORIGINS en .env (coma-separado)
# Ejemplo: CORS_ALLOWED_ORIGINS="https://app.mi-dominio.com,https://mi-frontend.cloudfront.net"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
