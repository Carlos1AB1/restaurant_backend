from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Review
from .serializers import ReviewSerializer
from apps.menu.models import Product # Para filtrar por producto

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso para permitir editar/borrar solo al dueño o admin.
    Lectura permitida para todos.
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para todos (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permisos de escritura solo para el dueño de la reseña o admin
        return obj.user == request.user or request.user.is_staff

class ReviewViewSet(mixins.CreateModelMixin,    # Crear reseñas
                   mixins.RetrieveModelMixin,  # Ver detalle de una reseña
                   mixins.UpdateModelMixin,    # Actualizar reseña (dueño/admin)
                   mixins.DestroyModelMixin,   # Eliminar reseña (dueño/admin)
                   mixins.ListModelMixin,      # Listar reseñas (aprobadas por defecto)
                   viewsets.GenericViewSet):
    """
    API endpoint para gestionar reseñas de productos.
    - Usuarios autenticados pueden crear reseñas (pendientes de aprobación).
    - Usuarios pueden ver/editar/eliminar SUS reseñas.
    - Admins pueden ver/editar/eliminar CUALQUIER reseña y aprobarlas.
    - Todos pueden listar las reseñas APROBADAS.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        """
        Filtra las reseñas:
        - Por defecto, solo muestra las aprobadas.
        - Si el usuario es admin, muestra todas.
        - Permite filtrar por producto (slug).
        """
        queryset = Review.objects.select_related('user', 'product').all()
        product_slug = self.request.query_params.get('product')

        if product_slug:
             # Obtener producto por slug o devolver 404 si no existe
             product = get_object_or_404(Product, slug=product_slug)
             queryset = queryset.filter(product=product)

        # Si el usuario no es admin, solo mostrar las aprobadas
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_approved=True)

        return queryset

    def perform_create(self, serializer):
        # El serializer ya asigna el usuario y pone is_approved=False
        # Asegúrate de pasar el context al serializer en la vista si es necesario
        # (GenericViewSet ya lo hace por defecto)
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, pk=product_id)
        serializer.save(user=self.request.user, product=product)
        # Podrías enviar notificación al admin aquí para moderar


    # Acción específica para que los admins aprueben reseñas
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser], url_path='approve')
    def approve_review(self, request, pk=None):
        review = self.get_object()
        if review.is_approved:
             return Response({'status': 'reseña ya aprobada'}, status=status.HTTP_400_BAD_REQUEST)
        review.is_approved = True
        review.save(update_fields=['is_approved', 'updated_at'])
        # La señal post_save se encargará de recalcular el promedio
        print(f"Admin {request.user.email} aprobó la reseña ID {review.pk}")
        return Response({'status': 'reseña aprobada'}, status=status.HTTP_200_OK)

    # Acción para desaprobar (por si acaso)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser], url_path='unapprove')
    def unapprove_review(self, request, pk=None):
        review = self.get_object()
        if not review.is_approved:
            return Response({'status': 'reseña ya está pendiente de aprobación'}, status=status.HTTP_400_BAD_REQUEST)
        review.is_approved = False
        review.save(update_fields=['is_approved', 'updated_at'])
        # La señal post_save recalculará
        print(f"Admin {request.user.email} desaprobó la reseña ID {review.pk}")
        return Response({'status': 'reseña desaprobada'}, status=status.HTTP_200_OK)