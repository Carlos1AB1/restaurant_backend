# Configuración para producción
import os
from .settings import *
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.prod
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.prod'))

# Seguridad
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Permitir DEBUG desde .env
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Configuración CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://3.17.68.60',
    'http://localhost',
    'http://127.0.0.1',
]

# Configuración de cookies
CSRF_COOKIE_SECURE = False  # True cuando tengas HTTPS
SESSION_COOKIE_SECURE = False  # True cuando tengas HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_AGE = 31449600  # 1 año
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

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

# Configuración de archivos estáticos para AWS S3
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Configuración de archivos estáticos y media
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Configuración de seguridad
SECURE_SSL_REDIRECT = False  # Deshabilitado para testing - habilitar cuando tengas HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Headers de seguridad adicionales
SECURE_CROSS_ORIGIN_OPENER_POLICY = None  # Deshabilitar para evitar advertencias en HTTP

# Configuración CORS para producción
CORS_ALLOW_ALL_ORIGINS = True  # Permitir todos los orígenes temporalmente
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://3.17.68.60',
    'http://localhost',
    'http://127.0.0.1',
]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# CORS para producción
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio-frontend.com",  # Actualizar con tu dominio
]

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
