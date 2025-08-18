#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de prueba.
Ejecuta este script con: python manage.py shell < populate_db.py
o python populate_db.py
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
if __name__ == '__main__':
    # Verificar si se pasó un argumento --settings
    settings_module = 'restaurant_backend.settings'
    for arg in sys.argv:
        if arg.startswith('--settings='):
            settings_module = arg.split('=')[1]
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    django.setup()

from django.contrib.auth import get_user_model
from apps.menu.models import Category, Product
from apps.reviews.models import Review
from apps.orders.models import Order, OrderItem

User = get_user_model()

def create_sample_data():
    print("🍽️  Creando datos de prueba para el restaurante...")
    
    # 1. Crear superusuario admin
    print("📋 Creando usuarios...")
    admin_user, created = User.objects.get_or_create(
        email='admin@restaurant.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Restaurant',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Admin creado: {admin_user.email}")
    else:
        print(f"ℹ️  Admin ya existe: {admin_user.email}")

    # 2. Crear usuarios de prueba
    test_users_data = [
        {'email': 'juan@example.com', 'first_name': 'Juan', 'last_name': 'Pérez'},
        {'email': 'maria@example.com', 'first_name': 'María', 'last_name': 'García'},
        {'email': 'carlos@example.com', 'first_name': 'Carlos', 'last_name': 'López'},
        {'email': 'ana@example.com', 'first_name': 'Ana', 'last_name': 'Martínez'},
    ]
    
    test_users = []
    for user_data in test_users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_active': True,
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"✅ Usuario creado: {user.email}")
        test_users.append(user)

    # 3. Crear repartidor
    deliverer, created = User.objects.get_or_create(
        email='repartidor@restaurant.com',
        defaults={
            'first_name': 'Pedro',
            'last_name': 'Delivery',
            'is_deliverer': True,
            'is_active': True,
        }
    )
    if created:
        deliverer.set_password('delivery123')
        deliverer.save()
        print(f"✅ Repartidor creado: {deliverer.email}")

    # 4. Crear categorías
    print("\n📂 Creando categorías...")
    categories_data = [
        {'name': 'Entrantes', 'description': 'Aperitivos y entradas para comenzar la comida'},
        {'name': 'Platos Principales', 'description': 'Nuestros platos principales más deliciosos'},
        {'name': 'Pizzas', 'description': 'Pizzas artesanales con ingredientes frescos'},
        {'name': 'Hamburguesas', 'description': 'Hamburguesas gourmet con carne de primera calidad'},
        {'name': 'Bebidas', 'description': 'Refrescos, jugos y bebidas especiales'},
        {'name': 'Postres', 'description': 'Dulces delicias para terminar tu comida'},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories[cat_data['name']] = category
        if created:
            print(f"✅ Categoría creada: {category.name}")

    # 5. Crear productos
    print("\n🍕 Creando productos...")
    products_data = [
        # Entrantes
        {'name': 'Alitas Buffalo', 'category': 'Entrantes', 'price': '8.50', 'description': 'Alitas de pollo crujientes bañadas en salsa buffalo picante, servidas con salsa ranch.'},
        {'name': 'Nachos Supremos', 'category': 'Entrantes', 'price': '9.95', 'description': 'Nachos crujientes con queso cheddar derretido, jalapeños, guacamole y crema agria.'},
        {'name': 'Calamares a la Romana', 'category': 'Entrantes', 'price': '10.50', 'description': 'Anillos de calamar frescos rebozados y fritos, servidos con salsa marinara.'},
        
        # Platos Principales
        {'name': 'Paella Valenciana', 'category': 'Platos Principales', 'price': '18.95', 'description': 'Auténtica paella valenciana con pollo, conejo, garrofó, judías verdes y azafrán.'},
        {'name': 'Salmón a la Plancha', 'category': 'Platos Principales', 'price': '16.50', 'description': 'Filete de salmón fresco a la plancha con verduras salteadas y salsa de limón.'},
        {'name': 'Cordero al Horno', 'category': 'Platos Principales', 'price': '22.00', 'description': 'Pierna de cordero al horno con hierbas aromáticas y patatas panaderas.'},
        
        # Pizzas
        {'name': 'Pizza Margherita', 'category': 'Pizzas', 'price': '12.95', 'description': 'Pizza clásica con salsa de tomate, mozzarella fresca y albahaca.'},
        {'name': 'Pizza Pepperoni Clásica', 'category': 'Pizzas', 'price': '14.50', 'description': 'Pizza con salsa de tomate, mozzarella y abundante pepperoni.'},
        {'name': 'Pizza Cuatro Quesos', 'category': 'Pizzas', 'price': '15.95', 'description': 'Deliciosa combinación de mozzarella, gorgonzola, parmesano y queso de cabra.'},
        {'name': 'Pizza Hawaiana', 'category': 'Pizzas', 'price': '13.95', 'description': 'Pizza con jamón, piña, mozzarella y salsa de tomate.'},
        
        # Hamburguesas
        {'name': 'Hamburguesa Clásica', 'category': 'Hamburguesas', 'price': '11.50', 'description': 'Carne de res 180g, lechuga, tomate, cebolla, pepinillos y salsa especial.'},
        {'name': 'Hamburguesa BBQ Bacon', 'category': 'Hamburguesas', 'price': '13.95', 'description': 'Carne de res, bacon crujiente, queso cheddar, aros de cebolla y salsa BBQ.'},
        {'name': 'Hamburguesa Vegetariana', 'category': 'Hamburguesas', 'price': '10.95', 'description': 'Hamburguesa de quinoa y verduras con aguacate, tomate y salsa de yogur.'},
        
        # Bebidas
        {'name': 'Coca-Cola', 'category': 'Bebidas', 'price': '2.50', 'description': 'Refrescante Coca-Cola original 350ml.'},
        {'name': 'Limonada Fresca Tropical', 'category': 'Bebidas', 'price': '3.95', 'description': 'Limonada natural con menta fresca y toque de jengibre.'},
        {'name': 'Agua Mineral', 'category': 'Bebidas', 'price': '1.95', 'description': 'Agua mineral natural 500ml.'},
        {'name': 'Cerveza Artesanal', 'category': 'Bebidas', 'price': '4.50', 'description': 'Cerveza artesanal local de trigo con notas cítricas.'},
        
        # Postres
        {'name': 'Tarta de Chocolate', 'category': 'Postres', 'price': '6.95', 'description': 'Deliciosa tarta de chocolate negro con cobertura de ganache.'},
        {'name': 'Helado de Vainilla Cono', 'category': 'Postres', 'price': '4.50', 'description': 'Cremoso helado artesanal de vainilla en cono crujiente.'},
        {'name': 'Flan Casero', 'category': 'Postres', 'price': '5.50', 'description': 'Flan tradicional casero con caramelo líquido.'},
        {'name': 'Tiramisú', 'category': 'Postres', 'price': '7.50', 'description': 'Tradicional tiramisú italiano con café y mascarpone.'},
    ]
    
    products = []
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            name=prod_data['name'],
            defaults={
                'category': categories[prod_data['category']],
                'description': prod_data['description'],
                'price': Decimal(prod_data['price']),
                'is_available': True,
            }
        )
        products.append(product)
        if created:
            print(f"✅ Producto creado: {product.name} - ${product.price}")

    # 6. Crear reseñas
    print("\n⭐ Creando reseñas...")
    reviews_data = [
        # Reseñas para Pizza Margherita
        {'product': 'Pizza Margherita', 'user': 0, 'rating': 5, 'comment': '¡Excelente pizza! La masa estaba perfecta y los ingredientes muy frescos.'},
        {'product': 'Pizza Margherita', 'user': 1, 'rating': 4, 'comment': 'Muy buena, aunque me hubiera gustado un poco más de albahaca.'},
        
        # Reseñas para Hamburguesa Clásica
        {'product': 'Hamburguesa Clásica', 'user': 2, 'rating': 5, 'comment': 'La mejor hamburguesa que he probado. Carne jugosa y pan fresco.'},
        {'product': 'Hamburguesa Clásica', 'user': 3, 'rating': 4, 'comment': 'Muy rica, buen tamaño de porción. Vendré otra vez.'},
        
        # Reseñas para Paella Valenciana
        {'product': 'Paella Valenciana', 'user': 0, 'rating': 5, 'comment': 'Auténtica paella, me recordó a Valencia. Perfectamente cocinada.'},
        {'product': 'Paella Valenciana', 'user': 2, 'rating': 4, 'comment': 'Muy sabrosa, aunque un poco salada para mi gusto.'},
        
        # Más reseñas variadas
        {'product': 'Alitas Buffalo', 'user': 1, 'rating': 4, 'comment': 'Picantes como me gustan. La salsa ranch complementa perfecto.'},
        {'product': 'Tarta de Chocolate', 'user': 3, 'rating': 5, 'comment': '¡Increíble postre! Súper chocolatoso y no empalagoso.'},
        {'product': 'Limonada Fresca Tropical', 'user': 2, 'rating': 5, 'comment': 'Refrescante y natural. Perfecto para el calor.'},
        {'product': 'Salmón a la Plancha', 'user': 0, 'rating': 4, 'comment': 'Pescado fresco y bien cocinado. Las verduras estaban deliciosas.'},
    ]
    
    for review_data in reviews_data:
        # Buscar el producto por nombre
        try:
            product = Product.objects.get(name=review_data['product'])
            user = test_users[review_data['user']]
            
            review, created = Review.objects.get_or_create(
                product=product,
                user=user,
                defaults={
                    'rating': review_data['rating'],
                    'comment': review_data['comment'],
                    'is_approved': True,  # Aprobar automáticamente para datos de prueba
                }
            )
            if created:
                print(f"✅ Reseña creada: {product.name} - {review.rating}⭐ por {user.first_name}")
        except Product.DoesNotExist:
            print(f"❌ Producto no encontrado: {review_data['product']}")

    # 7. Actualizar calificaciones promedio de productos
    print("\n📊 Actualizando calificaciones promedio...")
    for product in products:
        product.update_average_rating()
        if product.reviews.filter(is_approved=True).exists():
            print(f"✅ {product.name}: {product.average_rating:.1f}⭐")

    print("\n🎉 ¡Base de datos poblada exitosamente!")
    print("\n📝 Usuarios creados:")
    print("   👤 Admin: admin@restaurant.com (contraseña: admin123)")
    print("   👤 Usuario prueba: juan@example.com (contraseña: password123)")
    print("   👤 Usuario prueba: maria@example.com (contraseña: password123)")
    print("   👤 Usuario prueba: carlos@example.com (contraseña: password123)")
    print("   👤 Usuario prueba: ana@example.com (contraseña: password123)")
    print("   🚴 Repartidor: repartidor@restaurant.com (contraseña: delivery123)")
    print(f"\n📈 Resumen:")
    print(f"   📂 Categorías: {Category.objects.count()}")
    print(f"   🍽️  Productos: {Product.objects.count()}")
    print(f"   👥 Usuarios: {User.objects.count()}")
    print(f"   ⭐ Reseñas: {Review.objects.count()}")


if __name__ == '__main__':
    create_sample_data()
