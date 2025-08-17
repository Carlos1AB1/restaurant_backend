"""
Script de prueba para verificar que la API devuelve las imágenes de categorías
"""
import requests
import json

def test_categories_api():
    """
    Prueba el endpoint de categorías para verificar que incluye las imágenes
    """
    try:
        # URL del endpoint de categorías
        url = "http://localhost:8000/api/menu/categories/"
        
        print("🔍 Probando endpoint de categorías...")
        print(f"URL: {url}")
        
        # Hacer petición GET
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Respuesta exitosa!")
            
            # Parsear JSON
            data = response.json()
            
            # Verificar si es paginado o lista directa
            if isinstance(data, dict) and 'results' in data:
                categories = data['results']
                print(f"📋 Categorías encontradas (paginado): {len(categories)}")
            else:
                categories = data
                print(f"📋 Categorías encontradas: {len(categories)}")
            
            # Mostrar cada categoría y su imagen
            for i, category in enumerate(categories, 1):
                print(f"\n{i}. {category.get('name', 'Sin nombre')}")
                print(f"   Slug: {category.get('slug', 'N/A')}")
                print(f"   Activa: {category.get('is_active', 'N/A')}")
                
                image = category.get('image')
                if image:
                    print(f"   ✅ Imagen: {image}")
                else:
                    print(f"   ❌ Sin imagen")
                    
                description = category.get('description')
                if description:
                    print(f"   Descripción: {description[:50]}...")
            
            # Verificar campos esperados
            if categories:
                first_category = categories[0]
                expected_fields = ['id', 'name', 'slug', 'image', 'is_active']
                missing_fields = []
                
                for field in expected_fields:
                    if field not in first_category:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"\n⚠️  Campos faltantes en la respuesta: {missing_fields}")
                else:
                    print(f"\n✅ Todos los campos esperados están presentes")
                    
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("Asegúrate de que el servidor Django esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_products_api():
    """
    Prueba el endpoint de productos para verificar que incluye las imágenes
    """
    try:
        url = "http://localhost:8000/api/menu/products/"
        
        print("\n🔍 Probando endpoint de productos...")
        print(f"URL: {url}")
        
        response = requests.get(url, params={'limit': 3})  # Solo 3 productos para prueba
        
        if response.status_code == 200:
            print("✅ Respuesta exitosa!")
            
            data = response.json()
            
            if isinstance(data, dict) and 'results' in data:
                products = data['results']
                print(f"📋 Productos encontrados (paginado): {len(products)}")
            else:
                products = data
                print(f"📋 Productos encontrados: {len(products)}")
            
            for i, product in enumerate(products[:3], 1):  # Solo mostrar primeros 3
                print(f"\n{i}. {product.get('name', 'Sin nombre')}")
                print(f"   Categoría: {product.get('category', 'N/A')}")
                print(f"   Precio: {product.get('price', 'N/A')} €")
                
                image = product.get('image')
                if image:
                    print(f"   ✅ Imagen: {image}")
                else:
                    print(f"   ❌ Sin imagen")
                    
        else:
            print(f"❌ Error en la respuesta: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Probando API del Restaurante")
    print("=" * 50)
    
    test_categories_api()
    test_products_api()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas!")
    print("\n💡 Próximos pasos:")
    print("1. Si las categorías no tienen imágenes, ve al admin de Django")
    print("2. Edita cada categoría y sube una imagen")
    print("3. El frontend usará automáticamente estas imágenes")
