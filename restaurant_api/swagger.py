from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema


# Configuración personalizada para Swagger
class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        """
        Obtiene los tags para agrupar endpoints en la documentación.
        """
        tags = super().get_tags(operation_keys)

        # Personalizar tags basados en el path
        if operation_keys and len(operation_keys) >= 2:
            app_name = operation_keys[0]  # Nombre de la app (ej: 'users', 'menu', etc.)

            # Mapeo de apps a nombres más amigables
            app_name_mapping = {
                'users': 'Usuarios',
                'menu': 'Menú',
                'orders': 'Pedidos',
                'payments': 'Pagos',
                'chatbot': 'Chatbot',
                'search': 'Búsqueda'
            }

            if app_name in app_name_mapping:
                return [app_name_mapping[app_name]]

        return tags


# Definir información de la API
api_info = openapi.Info(
    title="Restaurant API",
    default_version='v1',
    description="""
    API para el sistema de restaurante que permite gestionar usuarios, menú, pedidos, pagos y más.

    ## Características principales

    * **Usuarios**: Registro, verificación por email, autenticación JWT, recuperación de contraseñas.
    * **Menú**: Gestión de categorías, platos, ingredientes, promociones y reseñas.
    * **Pedidos**: Carrito de compras, procesamiento de pedidos, historiales.
    * **Pagos**: Integración con Stripe para procesamiento de pagos.
    * **Chatbot**: Asistente virtual con capacidades de IA.
    * **Búsqueda**: Motor de búsqueda inteligente para platos.

    ## Autenticación

    La mayoría de los endpoints requieren autenticación mediante tokens JWT. Para autenticarte:

    1. Regístrate en `/api/v1/users/register/`
    2. Verifica tu email siguiendo el enlace enviado a tu correo
    3. Inicia sesión en `/api/v1/users/login/` para obtener los tokens
    4. Incluye el token de acceso en el header de autorización: `Authorization: Bearer <token>`

    Los tokens tienen una duración limitada, pero puedes refrescarlos en `/api/v1/users/token/refresh/`.
    """,
    terms_of_service="https://www.restaurant.com/terms/",
    contact=openapi.Contact(email="contact@restaurant.com"),
    license=openapi.License(name="MIT License"),
)

# Crear vista para el esquema de la API
schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# URLs para la documentación de la API
swagger_urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]