from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .swagger import swagger_urlpatterns

# Configuración de Swagger para documentación automática
schema_view = get_schema_view(
    openapi.Info(
        title="Restaurante API",
        default_version='v1',
        description="API para sistema de restaurante con Django REST Framework",
        terms_of_service="https://www.restaurant.com/terms/",
        contact=openapi.Contact(email="contact@restaurant.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger/json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API endpoints
    path('api/v1/users/', include('users.urls')),
    path('api/v1/menu/', include('menu.urls')),
    path('api/v1/orders/', include('orders.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/chatbot/', include('chatbot.urls')),
    path('api/v1/search/', include('search.urls')),
]

# Añadir los patrones de Swagger
urlpatterns += swagger_urlpatterns

# Servir archivos estáticos y de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)