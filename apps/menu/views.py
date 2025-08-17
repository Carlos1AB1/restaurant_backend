from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsAdminOrReadOnly # Permiso personalizado

# Permiso personalizado (opcional, puedes usar IsAdminUser directamente)
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo lectura a usuarios no administradores.
    """
    def has_permission(self, request, view):
        # Permite métodos seguros (GET, HEAD, OPTIONS) a cualquiera.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Requiere que el usuario sea staff (administrador) para otros métodos.
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para ver y editar categorías.
    Solo los administradores pueden crear, actualizar o eliminar.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly] # Solo admins pueden modificar
    lookup_field = 'slug' # Usar slug en lugar de ID en la URL

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Filtrar categorías activas para usuarios normales,
        mostrar todas para administradores.
        Siempre ordenar por campo order y luego por nombre.
        """
        queryset = Category.objects.all().order_by('order', 'name')
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint para ver y editar productos.
    Los administradores pueden gestionar productos.
    Los usuarios pueden ver la lista y detalles.
    """
    queryset = Product.objects.select_related('category').prefetch_related('reviews').all() # Optimización
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly] # Solo admins pueden modificar
    lookup_field = 'slug'

    # Filtros y Búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'is_available'] # Filtrar por slug de categoría y disponibilidad
    search_fields = ['name', 'description', 'category__name'] # Buscar por nombre, descripción, nombre de categoría
    ordering_fields = ['name', 'price', 'average_rating', 'created_at']
    ordering = ['name'] # Orden por defecto

    # Sobrescribir get_queryset si quieres filtrar productos no disponibles para usuarios normales
    # def get_queryset(self):
    #    queryset = super().get_queryset()
    #    if not self.request.user.is_staff:
    #        queryset = queryset.filter(is_available=True)
    #    return queryset

    # El perform_create, perform_update, perform_destroy ya están manejados
    # por ModelViewSet y los permisos controlan quién puede ejecutarlos.