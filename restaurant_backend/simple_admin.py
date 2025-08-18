from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from apps.menu.models import Category, Product
from apps.users.models import User
from apps.orders.models import Order
import json

@csrf_exempt
def simple_admin_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            user = authenticate(request, username=email, password=password)
            if user and user.is_staff:
                login(request, user)
                return JsonResponse({'success': True, 'redirect': '/simple-admin/dashboard/'})
            else:
                return JsonResponse({'success': False, 'error': 'Credenciales inválidas'})
        except:
            pass
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 10px; background: #007cba; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #005a8b; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ Restaurant Admin</h1>
            <form id="loginForm">
                <input type="email" id="email" placeholder="Email" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div id="message"></div>
        </div>
        
        <script>
            document.getElementById('loginForm').onsubmit = function(e) {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                fetch('/simple-admin/login/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect;
                    } else {
                        document.getElementById('message').innerHTML = '<p style="color: red;">' + data.error + '</p>';
                    }
                });
            };
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)

@user_passes_test(lambda u: u.is_staff)
def simple_admin_dashboard(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    users = User.objects.all()
    orders = Order.objects.all()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restaurant Admin Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #007cba; color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .table th {{ background: #f8f9fa; }}
            .logout {{ float: right; background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ Restaurant Admin Dashboard</h1>
            <a href="/simple-admin/logout/" class="logout">Logout</a>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{categories.count()}</h3>
                    <p>Categorías</p>
                </div>
                <div class="stat-card">
                    <h3>{products.count()}</h3>
                    <p>Productos</p>
                </div>
                <div class="stat-card">
                    <h3>{users.count()}</h3>
                    <p>Usuarios</p>
                </div>
                <div class="stat-card">
                    <h3>{orders.count()}</h3>
                    <p>Pedidos</p>
                </div>
            </div>
            
            <h2>📋 Categorías</h2>
            <table class="table">
                <tr><th>ID</th><th>Nombre</th><th>Descripción</th></tr>
                {''.join([f'<tr><td>{c.id}</td><td>{c.name}</td><td>{c.description}</td></tr>' for c in categories])}
            </table>
            
            <h2>🍔 Productos (Últimos 10)</h2>
            <table class="table">
                <tr><th>ID</th><th>Nombre</th><th>Precio</th><th>Categoría</th></tr>
                {''.join([f'<tr><td>{p.id}</td><td>{p.name}</td><td>${p.price}</td><td>{p.category.name}</td></tr>' for p in products[:10]])}
            </table>
            
            <h2>📝 Pedidos Recientes</h2>
            <table class="table">
                <tr><th>ID</th><th>Usuario</th><th>Total</th><th>Estado</th><th>Fecha</th></tr>
                {''.join([f'<tr><td>{o.id}</td><td>{o.user.email}</td><td>${o.total_price}</td><td>{o.status}</td><td>{o.created_at.strftime("%Y-%m-%d %H:%M")}</td></tr>' for o in orders[:10]])}
            </table>
            
            <p><strong>🔗 Enlaces útiles:</strong></p>
            <ul>
                <li><a href="/swagger/" target="_blank">📖 Documentación API</a></li>
                <li><a href="/api/menu/categories/" target="_blank">🍕 API Categorías</a></li>
                <li><a href="/api/menu/products/" target="_blank">🍔 API Productos</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

@user_passes_test(lambda u: u.is_staff)
def simple_admin_logout(request):
    logout(request)
    return redirect('/simple-admin/login/')
