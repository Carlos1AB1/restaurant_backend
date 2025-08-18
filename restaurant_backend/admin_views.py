from django.shortcuts import redirect
from django.middleware.csrf import get_token
from django.http import HttpResponse
from django.template.context_processors import csrf
from django.template import RequestContext, Template

def admin_csrf_fix(request):
    """Vista para establecer la cookie CSRF antes de redirigir al admin"""
    # Forzar la creación del token CSRF
    csrf_token = get_token(request)
    
    # Opción 1: Página intermedia que establece el token y luego redirige
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configurando Admin...</title>
        <meta http-equiv="refresh" content="2;url=/admin/">
    </head>
    <body>
        <div style="text-align: center; margin: 100px; font-family: Arial;">
            <h2>🔧 Configurando acceso al administrador...</h2>
            <p>Serás redirigido automáticamente en 2 segundos.</p>
            <p>Si no eres redirigido, <a href="/admin/">haz clic aquí</a>.</p>
        </div>
        
        <!-- Token CSRF oculto para establecer la cookie -->
        <form style="display: none;">
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
        </form>
        
        <script>
            // Establecer cookie CSRF manualmente si no existe
            if (!document.cookie.includes('csrftoken=')) {{
                document.cookie = 'csrftoken={csrf_token}; path=/; samesite=lax';
            }}
            
            // Redirigir después de 2 segundos
            setTimeout(function() {{
                window.location.href = '/admin/';
            }}, 2000);
        </script>
    </body>
    </html>
    """
    
    response = HttpResponse(html)
    
    # Asegurar que la cookie CSRF se establezca correctamente
    response.set_cookie(
        'csrftoken', 
        csrf_token,
        max_age=31449600,  # 1 año
        domain=None,
        path='/',
        secure=request.is_secure(),  # True si HTTPS, False si HTTP
        httponly=False,
        samesite='Lax'
    )
    
    return response

def admin_direct_access(request):
    """Vista alternativa para acceder directamente al admin con CSRF configurado"""
    from django.contrib.admin import site
    
    # Obtener el token CSRF
    csrf_token = get_token(request)
    
    # Si ya está autenticado, redirigir al admin
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin/')
    
    # Si no está autenticado, mostrar enlace al admin con token
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restaurant Admin Access</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .admin-link {{ display: inline-block; padding: 15px 30px; background: #417690; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            .admin-link:hover {{ background: #2e5c72; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ Restaurant Admin</h1>
            <p>Accede al panel de administración de Django.</p>
            
            <a href="/admin/" class="admin-link">🔐 Ir al Admin de Django</a><br>
            <a href="/simple-admin/" class="admin-link">⚡ Admin Simplificado</a>
            
            <!-- Token CSRF oculto -->
            <form style="display: none;">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
            </form>
        </div>
        
        <script>
            // Establecer cookie CSRF
            document.cookie = 'csrftoken={csrf_token}; path=/; samesite=lax';
        </script>
    </body>
    </html>
    """
    
    response = HttpResponse(html)
    response.set_cookie(
        'csrftoken', 
        csrf_token,
        max_age=31449600,
        domain=None,
        path='/',
        secure=request.is_secure(),
        httponly=False,
        samesite='Lax'
    )
    
    return response