# Configuración para producción - CSRF Fix
import os
from .settings import *
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.prod
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.prod'))

# Seguridad
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Permitir DEBUG desde .env
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

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

# Configuración de archivos estáticos para AWS S3 (opcional)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Si tienes configurado S3, usar esto:
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # Si no usas S3, usar archivos locales
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ===== CONFIGURACIÓN CSRF - FIX PRINCIPAL =====

# 1. Configuración básica de CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://3.17.68.60',
    'https://3.17.68.60',
    'http://localhost',
    'http://127.0.0.1',
]

# 2. Configuración de cookies CSRF
CSRF_COOKIE_SECURE = False  # Cambiar a True cuando tengas HTTPS
CSRF_COOKIE_HTTPONLY = False  # Permitir que JavaScript acceda si es necesario
CSRF_COOKIE_SAMESITE = 'Lax'  # Más permisivo que 'Strict'
CSRF_COOKIE_NAME = 'csrftoken'

# 3. Configuración de cookies de sesión
SESSION_COOKIE_SECURE = False  # Cambiar a True cuando tengas HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 horas

# ===== CONFIGURACIÓN CORS =====
CORS_ALLOW_ALL_ORIGINS = True  # Para desarrollo/testing
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://3.17.68.60',
    'http://localhost:3000',
    'http://localhost:8080',
    'http://127.0.0.1:3000',
]

# Headers CORS adicionales
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ===== CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN =====

# Configuración de proxy reverso (Nginx)
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Headers de seguridad - MÁS PERMISIVOS TEMPORALMENTE
SECURE_SSL_REDIRECT = False  # Mantener False hasta tener HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Deshabilitar temporalmente para evitar conflictos
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = None

# ===== MIDDLEWARE - ORDEN IMPORTANTE =====
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS debe ir primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF después de común
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===== LOGGING =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/tmp/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# ===== CONFIGURACIÓN ADICIONAL =====

# Timeout de sesión
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Cache (opcional - mejora rendimiento)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}