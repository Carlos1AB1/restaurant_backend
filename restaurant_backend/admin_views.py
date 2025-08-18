from django.shortcuts import redirect
from django.middleware.csrf import get_token
from django.http import HttpResponse

def admin_csrf_fix(request):
    """Vista para establecer la cookie CSRF antes de redirigir al admin"""
    # Forzar la creación del token CSRF
    csrf_token = get_token(request)
    
    # Crear respuesta de redirección al admin
    response = redirect('/admin/')
    
    # Asegurar que la cookie CSRF se establezca
    response.set_cookie(
        'csrftoken', 
        csrf_token,
        max_age=31449600,  # 1 año
        domain=None,
        path='/',
        secure=False,  # True cuando tengas HTTPS
        httponly=False,
        samesite='Lax'
    )
    
    return response
