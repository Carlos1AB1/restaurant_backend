"""
Script para actualizar las categorías existentes con imágenes por defecto
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_backend.settings')
django.setup()

from apps.menu.models import Category

def update_categories_with_default_images():
    """
    Actualiza las categorías existentes para que todas estén activas
    y define imágenes por defecto basadas en sus nombres
    """
    
    # Mapeo de categorías a imágenes por defecto (usando las del frontend)
    default_images = {
        'hamburguesas': 'category_images/hamburguesas/burger.png',
        'pizzas': 'category_images/pizzas/pizza.png', 
        'bebidas': 'category_images/bebidas/bebida.png',
        'postres': 'category_images/postres/postres.png',
        'ensaladas': 'category_images/ensaladas/ensalada.png',
        'pasta': 'category_images/pasta/pasta.png',
        'pollo': 'category_images/pollo/pollo.png',
    }
    
    # Actualizar todas las categorías para que estén activas
    Category.objects.all().update(is_active=True)
    print("✅ Todas las categorías marcadas como activas")
    
    # Mostrar categorías existentes
    categories = Category.objects.all()
    print(f"\n📋 Categorías encontradas ({categories.count()}):")
    
    for category in categories:
        print(f"  - {category.name} (slug: {category.slug})")
        
        # Buscar imagen por defecto basada en el nombre de la categoría
        image_assigned = False
        for keyword, image_path in default_images.items():
            if keyword.lower() in category.name.lower() or keyword.lower() in category.slug.lower():
                # Solo asignar imagen si no tiene una ya
                if not category.image:
                    # Nota: En un entorno real, copiarías las imágenes físicamente
                    # Por ahora solo mostramos qué imagen debería tener
                    print(f"    → Debería tener imagen: {image_path}")
                else:
                    print(f"    → Ya tiene imagen: {category.image}")
                image_assigned = True
                break
        
        if not image_assigned and not category.image:
            print(f"    → Sin imagen asignada (usar imagen por defecto)")
    
    print(f"\n💡 Para completar la configuración:")
    print("1. Sube imágenes desde el panel de administración de Django")
    print("2. Ve a /admin/menu/category/ y edita cada categoría")
    print("3. Las imágenes se organizarán automáticamente en media/category_images/")

if __name__ == "__main__":
    update_categories_with_default_images()
