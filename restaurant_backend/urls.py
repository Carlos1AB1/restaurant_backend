from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from apps.users.views import VerifyEmailView
from .admin_views import admin_csrf_fix

def home_view(request):
    """Vista de bienvenida que redirige a la documentación de la API"""
    return redirect('schema-swagger-ui')

def api_info(request):
    """Vista simple con información de la API"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restaurant API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #d4a574; text-align: center; }
            .links { text-align: center; margin: 20px 0; }
            .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #d4a574; color: white; text-decoration: none; border-radius: 5px; }
            .links a:hover { background: #b8956a; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #d4a574; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ Restaurant API</h1>
            <p>Bienvenido a la API del restaurante. Esta API permite gestionar menús, pedidos, usuarios y más.</p>
            
            <div class="links">
                <a href="/swagger/">📖 Documentación API (Swagger)</a>
                <a href="/redoc/">📚 Documentación API (ReDoc)</a>
                <a href="/admin/">⚙️ Panel de Administración</a>
            </div>
            
            <h3>🔗 Endpoints principales:</h3>
            <div class="endpoint"><strong>GET /api/menu/categories/</strong> - Listar categorías</div>
            <div class="endpoint"><strong>GET /api/menu/products/</strong> - Listar productos</div>
            <div class="endpoint"><strong>POST /api/users/register/</strong> - Registrar usuario</div>
            <div class="endpoint"><strong>POST /api/users/login/</strong> - Iniciar sesión</div>
            <div class="endpoint"><strong>GET /api/orders/</strong> - Listar pedidos (autenticado)</div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                💾 Base de datos poblada con datos de prueba.<br>
                👤 Admin: admin@restaurant.com (contraseña: admin123)
            </p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

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
    # Página de inicio
    path('', api_info, name='home'),
    
    # Ruta especial para admin que configura CSRF
    path('admin-setup/', admin_csrf_fix, name='admin_csrf_fix'),
    path('admin/', admin.site.urls),
    # path('', include('admin_atlantis.urls')),

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
