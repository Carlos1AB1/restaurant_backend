from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from apps.users.views import VerifyEmailView

schema_view = get_schema_view(
    openapi.Info(
        title="Restaurant API",
        default_version='v1',
        description="API para la gestión de un restaurante",
        terms_of_service="https://www.google.com/policies/terms/",  # Cambia esto
        contact=openapi.Contact(email=settings.RESTAURANT_CONTACT_EMAIL),
        license=openapi.License(name="BSD License"),  # Cambia esto si aplica
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('admin_atlantis.urls')),

    # API Endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/chatbot/', include('apps.chatbot.urls')),
    path('api/contact/', include('apps.contact.urls')),
    path('api/delivery/', include('apps.delivery.urls')),
    path('api/invoices/', include('apps.invoices.urls')),
    path('users/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),

    # Documentación API (Swagger/Redoc)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]

# Servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
