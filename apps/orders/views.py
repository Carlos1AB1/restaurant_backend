from rest_framework import viewsets, status, generics, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer, CartItemSerializer, OrderSerializer, CreateOrderSerializer,
    OrderStatusUpdateSerializer, AssignDelivererSerializer
)
from apps.menu.models import Product
from .permissions import IsOwnerOrAdmin, IsAdminOrDeliverer, IsAssignedDelivererOrAdmin  # Añadido nuevo permiso


# --- Permisos ---
class IsOwnerOrAdmin(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # Permite al dueño del objeto o a un admin verlo/editarlo
        if isinstance(obj, Cart):
            return obj.user == request.user or request.user.is_staff
        if isinstance(obj, Order):
            return obj.user == request.user or request.user.is_staff
        return False


class IsAdminOrDeliverer(IsAuthenticated):
    def has_permission(self, request, view):
        # Permite acceso a admins o repartidores
        return request.user and (request.user.is_staff or request.user.is_deliverer)


class IsAssignedDelivererOrAdmin(IsAuthenticated):
    """
    Permite acceso solo al repartidor asignado a la orden o a un admin.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        # Admin siempre tiene permiso
        if request.user.is_staff:
            return True
        # Repartidor tiene permiso si está asignado a esta orden específica
        return hasattr(request.user, 'is_deliverer') and request.user.is_deliverer and obj.assigned_to == request.user


# --- Carrito de Compras ---

class CartViewSet(viewsets.ViewSet):
    """
    Gestiona el carrito de compras del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get_cart(self, user):
        # Obtiene o crea el carrito para el usuario
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    @action(detail=False, methods=['get'], url_path='my-cart')
    def my_cart(self, request):
        """Obtiene el carrito del usuario actual."""
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """Añade un producto al carrito o actualiza la cantidad."""
        cart = self.get_cart(request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            return Response({"error": "La cantidad debe ser positiva."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado o no disponible."}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            # Si ya existe, actualiza la cantidad
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='update-item/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        """Actualiza la cantidad de un item en el carrito."""
        cart = self.get_cart(request.user)
        quantity = int(request.data.get('quantity'))

        if quantity <= 0:
            return Response({"error": "La cantidad debe ser al menos 1."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.quantity = quantity
            cart_item.save()
            serializer = CartSerializer(cart, context={'request': request})
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({"error": "Item no encontrado en el carrito."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Cantidad inválida."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'], url_path='remove-item/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        """Elimina un item del carrito."""
        cart = self.get_cart(request.user)
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            serializer = CartSerializer(cart, context={'request': request})
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({"error": "Item no encontrado en el carrito."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete'], url_path='clear-cart')
    def clear_cart(self, request):
        """Vacía el carrito del usuario."""
        cart = self.get_cart(request.user)
        cart.clear()
        return Response({"message": "Carrito vaciado exitosamente."}, status=status.HTTP_204_NO_CONTENT)


# --- Pedidos ---

class OrderViewSet(viewsets.ModelViewSet):
    """
    Gestiona los pedidos. Los usuarios pueden crear y ver sus pedidos.
    Los administradores pueden ver todos y actualizar estados.
    Los repartidores pueden ver los pedidos asignados.
    """
    serializer_class = OrderSerializer

    # queryset = Order.objects.all() # Sobrescribir get_queryset para filtrar

    def get_permissions(self):
        """Permisos basados en la acción."""
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['list', 'retrieve']:
            # Usuarios ven los suyos, admins/repartidores ven más (filtrado en get_queryset)
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            # Solo admins pueden modificar/eliminar pedidos completos (cancelar es acción separada)
            return [IsAdminUser()]
        if self.action in ['update_status', 'assign_deliverer']:
            return [IsAdminUser()]  # Solo Admins
        if self.action == 'my_assigned_orders':
            return [IsAdminOrDeliverer()]  # Repartidores y Admins
        if self.action == 'cancel_order':
            return [IsOwnerOrAdmin()]  # Dueño o Admin pueden intentar cancelar
        if self.action == 'mark_as_delivered':
            return [IsAssignedDelivererOrAdmin()]  # Repartidor asignado o Admin
        return [IsAuthenticated()]  # Permiso por defecto

    def get_queryset(self):
        """Filtra pedidos según el rol del usuario."""
        user = self.request.user
        if user.is_staff:
            # Admins ven todos los pedidos
            return Order.objects.prefetch_related('items', 'user').all()
        elif hasattr(user, 'is_deliverer') and user.is_deliverer:
            # Repartidores ven los pedidos que tienen asignados
            # Opcional: podrían ver también los 'PROCESSING'/'SCHEDULED' sin asignar? Depende de la lógica de negocio
            return Order.objects.filter(assigned_to=user).prefetch_related('items', 'user')
        else:
            # Usuarios normales ven solo sus propios pedidos
            return Order.objects.filter(user=user).prefetch_related('items')

    @transaction.atomic  # Asegura que la creación del pedido y limpieza del carrito sean atómicas
    def create(self, request, *args, **kwargs):
        """Crea un nuevo pedido a partir del carrito del usuario."""
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = request.user
        try:
            cart = Cart.objects.prefetch_related('items__product').get(user=user)
        except Cart.DoesNotExist:
            return Response({"error": "Carrito no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({"error": "El carrito está vacío."}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular precio total desde el carrito (más seguro que confiar en el frontend)
        total_price = cart.get_total_price()

        # Crear el pedido
        order_data = {
            'user': user,
            'total_price': total_price,
            'delivery_address': validated_data['delivery_address'],
            'phone_number': validated_data['phone_number'],
            'notes': validated_data.get('notes'),
            'is_scheduled': validated_data.get('is_scheduled', False),
            'scheduled_datetime': validated_data.get('scheduled_datetime')
            # El estado se establecerá en PENDING o SCHEDULED en el save() del modelo
        }
        order = Order(**order_data)
        order.save()  # Llama al save personalizado que genera nº pedido y ajusta estado

        # Crear los items del pedido desde el carrito
        order_items = []
        for cart_item in cart.items.all():
            # Verificar disponibilidad de nuevo por si acaso
            if not cart_item.product.is_available:
                # Podrías lanzar error o simplemente omitir el item
                transaction.set_rollback(True)  # Revertir la creación del pedido
                return Response({"error": f"El producto '{cart_item.product.name}' ya no está disponible."},
                                status=status.HTTP_400_BAD_REQUEST)

            order_items.append(OrderItem(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,  # Guardar nombre actual
                price=cart_item.product.price,  # Guardar precio actual
                quantity=cart_item.quantity
            ))
        OrderItem.objects.bulk_create(order_items)

        # Vaciar el carrito
        cart.clear()

        # Devolver el pedido creado (usa el serializer de lectura)
        order_serializer = OrderSerializer(order, context={'request': request})
        # La señal post_save se encargará de enviar email/generar factura si está configurada
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        """Permite a un usuario (o admin) cancelar su pedido si está dentro del límite de tiempo."""
        order = self.get_object()  # Obtiene el pedido usando get_queryset y pk
        self.check_object_permissions(request, order)  # Verifica permiso IsOwnerOrAdmin

        if order.status == 'CANCELLED':
            return Response({"message": "El pedido ya está cancelado."}, status=status.HTTP_400_BAD_REQUEST)

        if order.can_cancel():
            original_status = order.status
            order.status = 'CANCELLED'
            order.save(update_fields=['status', 'updated_at'])
            # Aquí podrías añadir lógica adicional (ej. revertir stock si lo gestionas)
            # y enviar una notificación de cancelación.
            print(
                f"Pedido {order.order_number} cancelado por usuario {request.user.email}. Estado anterior: {original_status}")
            return Response({"message": "Pedido cancelado exitosamente."}, status=status.HTTP_200_OK)
        else:
            # Determinar la razón
            reason = "Ha pasado el tiempo límite para la cancelación."
            if order.status not in ['PENDING', 'PROCESSING', 'SCHEDULED']:
                reason = f"No se puede cancelar un pedido en estado '{order.get_status_display()}'."
            elif order.is_scheduled and order.scheduled_datetime and not order.can_cancel():
                reason = "Es demasiado tarde para cancelar un pedido programado."

            return Response({"error": reason}, status=status.HTTP_400_BAD_REQUEST)

    # Acciones específicas para Administradores
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser], url_path='update-status')
    def update_status(self, request, pk=None):
        """Actualiza el estado de un pedido (solo Admin)."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Podrías añadir validaciones de transiciones de estado aquí si es necesario
        # Ej: No pasar de DELIVERED a PENDING
        new_status = serializer.validated_data.get('status')
        print(f"Admin {request.user.email} actualizando estado del pedido {order.order_number} a {new_status}")
        serializer.save()
        # Devolver el pedido actualizado completo
        full_serializer = OrderSerializer(order, context={'request': request})
        return Response(full_serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser], url_path='assign-deliverer')
    def assign_deliverer(self, request, pk=None):
        """Asigna un repartidor a un pedido (solo Admin)."""
        order = self.get_object()
        serializer = AssignDelivererSerializer(order, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        deliverer = serializer.validated_data.get('assigned_to')
        print(
            f"Admin {request.user.email} asignando pedido {order.order_number} a repartidor {deliverer.email if deliverer else 'Nadie'}")

        # Opcional: Cambiar estado a 'OUT_FOR_DELIVERY' al asignar? O dejarlo manual?
        # if deliverer and order.status in ['PROCESSING', 'SCHEDULED']:
        #    order.status = 'OUT_FOR_DELIVERY'

        serializer.save()
        # Devolver el pedido actualizado completo
        full_serializer = OrderSerializer(order, context={'request': request})
        return Response(full_serializer.data)

    # Acción para Repartidores
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrDeliverer], url_path='my-assigned')
    def my_assigned_orders(self, request):
        """Devuelve los pedidos asignados al repartidor actual."""
        # get_queryset ya filtra por repartidor si el usuario es is_deliverer
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_as_delivered(self, request, pk=None):
        """
        Permite al repartidor asignado (o a un admin) marcar el pedido como entregado.
        """
        order = self.get_object()
        # get_permissions y has_object_permission (via IsAssignedDelivererOrAdmin) ya validan el acceso

        # Validar que el pedido esté en un estado apropiado para ser entregado
        # Por ejemplo, debe estar 'En Reparto'
        if order.status != 'OUT_FOR_DELIVERY':
            return Response(
                {
                    "error": f"Solo se puede marcar como entregado un pedido que está 'En Reparto'. Estado actual: {order.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status == 'DELIVERED':
            return Response({'message': 'El pedido ya figura como entregado.'}, status=status.HTTP_200_OK)

        order.status = 'DELIVERED'
        order.save(update_fields=['status', 'updated_at'])

        # La señal post_save (si está configurada) podría enviar notificación al cliente
        print(
            f"Pedido {order.order_number} marcado como ENTREGADO por {'Admin' if request.user.is_staff else 'Repartidor'} {request.user.email}")

        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)