from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer, CartItemSerializer,
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
)
from menu.models import Dish


class CartView(generics.RetrieveAPIView):
    """
    Vista para obtener el carrito del usuario actual.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Obtiene o crea el carrito para el usuario actual."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemViewSet(viewsets.ModelViewSet):
    """
    Viewset para gestionar ítems del carrito.
    """
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna los ítems del carrito del usuario actual."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def perform_create(self, serializer):
        """Asigna el carrito del usuario actual al crear un ítem."""
        serializer.save()

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Endpoint para vaciar el carrito."""
        try:
            cart = Cart.objects.get(user=request.user)
            cart.clear()
            return Response(
                {"detail": _("Carrito vaciado correctamente.")},
                status=status.HTTP_200_OK
            )
        except Cart.DoesNotExist:
            return Response(
                {"detail": _("El carrito no existe.")},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderViewSet(viewsets.ModelViewSet):
    """
    Viewset para gestionar pedidos.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Retorna los pedidos del usuario actual."""
        user = self.request.user

        # Los administradores pueden ver todos los pedidos
        if user.is_staff:
            queryset = Order.objects.all()

            # Filtrar por usuario si se proporciona el ID
            user_id = self.request.query_params.get('user_id', None)
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            # Usuarios normales solo ven sus propios pedidos
            queryset = Order.objects.filter(user=user)

        # Filtrar por estado si se proporciona
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filtrar por fecha
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    def get_permissions(self):
        """
        Personalizar permisos:
        - Listado y detalle: usuario autenticado
        - Actualizar estado: solo admin
        - Crear: usuario autenticado
        - Eliminar: nadie (no se permite eliminar pedidos)
        """
        if self.action in ['update', 'partial_update']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_status(self, request, pk=None):
        """Endpoint para actualizar el estado de un pedido."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.update(order, serializer.validated_data)
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Endpoint para obtener pedidos activos del usuario."""
        active_statuses = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'OUT_FOR_DELIVERY']
        orders = Order.objects.filter(
            user=request.user,
            status__in=active_statuses
        ).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class CheckoutView(generics.CreateAPIView):
    """
    Vista para crear un pedido a partir del carrito (checkout).
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Retornar datos del pedido creado
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )