from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils.translation import gettext_lazy as _

from .models import Category, Dish, Ingredient, DishIngredient, Promotion, Review
from .serializers import (
    CategoryListSerializer, CategoryDetailSerializer,
    DishListSerializer, DishDetailSerializer, DishCreateUpdateSerializer,
    IngredientSerializer, DishIngredientSerializer,
    PromotionSerializer, PromotionDetailSerializer,
    ReviewSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para solo permitir administradores
    modificar objetos. Lectura permitida para todos.
    """

    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS para cualquier usuario
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permitir escritura solo a administradores
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset para CRUD de categorías.
    """
    queryset = Category.objects.filter(is_active=True).annotate(
        dish_count=Count('dishes', filter=Q(dishes__is_active=True))
    )
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'order']
    ordering = ['order']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategoryListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por nombre si se proporciona
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class DishViewSet(viewsets.ModelViewSet):
    """
    Viewset para CRUD de platos.
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'category__name']
    ordering = ['category__order', 'name']

    def get_queryset(self):
        queryset = Dish.objects.filter(is_active=True).select_related('category')

        # Filtrar por categoría si se proporciona
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filtrar platos destacados si se solicita
        featured = self.request.query_params.get('featured', None)
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        # Filtrar por rango de precios si se proporciona
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DishCreateUpdateSerializer
        elif self.action == 'retrieve':
            return DishDetailSerializer
        return DishListSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, pk=None):
        """
        Endpoint para agregar una reseña a un plato.
        """
        dish = self.get_object()

        # Verificar si el usuario ya ha hecho una reseña para este plato
        if Review.objects.filter(dish=dish, user=request.user).exists():
            return Response(
                {"detail": _("Ya has realizado una reseña para este plato.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save(dish=dish, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """
        Endpoint para obtener platos recomendados (mejor calificados).
        """
        dishes = Dish.objects.filter(is_active=True).annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]

        serializer = DishListSerializer(dishes, many=True)
        return Response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Viewset para CRUD de ingredientes.
    """
    queryset = Ingredient.objects.filter(is_active=True)
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar alérgenos si se solicita
        allergen = self.request.query_params.get('allergen', None)
        if allergen and allergen.lower() == 'true':
            queryset = queryset.filter(is_allergen=True)

        return queryset


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Viewset para CRUD de promociones.
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'name']
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = Promotion.objects.filter(is_active=True)

        # Filtrar promociones activas si se solicita
        active = self.request.query_params.get('active', None)
        if active and active.lower() == 'true':
            from django.utils import timezone
            now = timezone.now()
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PromotionDetailSerializer
        return PromotionSerializer

    @action(detail=True, methods=['post'])
    def add_dishes(self, request, pk=None):
        """
        Endpoint para agregar platos a una promoción.
        """
        promotion = self.get_object()
        dish_ids = request.data.get('dish_ids', [])

        if not dish_ids:
            return Response(
                {"detail": _("No se proporcionaron IDs de platos.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        dishes = Dish.objects.filter(id__in=dish_ids, is_active=True)

        if len(dishes) != len(dish_ids):
            return Response(
                {"detail": _("Algunos platos no existen o no están activos.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        promotion.dishes.add(*dishes)
        return Response(
            {"detail": _("Platos agregados a la promoción correctamente.")},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def remove_dishes(self, request, pk=None):
        """
        Endpoint para eliminar platos de una promoción.
        """
        promotion = self.get_object()
        dish_ids = request.data.get('dish_ids', [])

        if not dish_ids:
            return Response(
                {"detail": _("No se proporcionaron IDs de platos.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        dishes = Dish.objects.filter(id__in=dish_ids)
        promotion.dishes.remove(*dishes)

        return Response(
            {"detail": _("Platos eliminados de la promoción correctamente.")},
            status=status.HTTP_200_OK
        )