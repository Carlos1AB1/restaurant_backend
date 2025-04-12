# restaurant_backend/apps/orders/serializers.py

from datetime import timedelta
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings # Importar settings

from .models import Cart, CartItem, Order, OrderItem
from apps.menu.serializers import ProductSerializer
from apps.menu.models import Product

# Get the User model
User = get_user_model()

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_available=True),
        source='product',
        write_only=True
    )
    total_price = serializers.DecimalField(source='get_total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser al menos 1.")
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(source='get_total_price', max_digits=10, decimal_places=2, read_only=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(source='product_name')
    total_price = serializers.DecimalField(source='get_total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True) # User no debe ser editable en un pedido existente
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # --- CORRECCIÓN AQUÍ ---
    can_cancel = serializers.BooleanField(read_only=True) # Eliminado source='can_cancel'
    # --- FIN CORRECCIÓN ---
    # Opcional: Mostrar info más detallada del repartidor
    assigned_to_info = serializers.StringRelatedField(source='assigned_to', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'items', 'total_price', 'status', 'status_display',
            'delivery_address', 'phone_number', 'notes',
            'is_scheduled', 'scheduled_datetime',
            'assigned_to', # ID para asignación (write-only si usas otra vista/serializer para asignar)
            'assigned_to_info', # Info legible del repartidor (read-only)
            'created_at', 'updated_at',
            'can_cancel' # Incluido el campo corregido
        ]
        # Read only fields gestionados por el sistema o que no deben cambiar post-creación
        read_only_fields = [
            'id', 'order_number', 'user', 'items', # items se leen, no se escriben aquí
            'total_price', # Calculado
            'status_display', # Derivado
            'assigned_to_info', # Derivado
            'created_at', 'updated_at',
            'can_cancel' # Derivado y ya marcado como read_only=True arriba
        ]
        # Campos que podrían ser escritos en Ciertas Vistas/Acciones
        # (ej: status, assigned_to, delivery_address, phone_number, notes, is_scheduled, scheduled_datetime)
        # Usaremos serializers específicos (OrderStatusUpdate, AssignDeliverer, etc.) para modificarlos
        # Para la vista principal (lectura/listado), muchos serán read-only implícitamente.
        # Si usaras este serializer para actualizar TODO el pedido (no recomendado), necesitarías
        # quitar campos de read_only_fields.


    # La validación de scheduled_datetime ya está bien en tu código original.
    # No se necesita modificar aquí.
    def validate(self, data):
        is_scheduled = data.get('is_scheduled', getattr(self.instance, 'is_scheduled', False))
        scheduled_datetime = data.get('scheduled_datetime', getattr(self.instance, 'scheduled_datetime', None))

        if is_scheduled:
            if not scheduled_datetime:
                raise serializers.ValidationError({"scheduled_datetime": "Debe proporcionar una fecha y hora para pedidos programados."})
            # Usar timezone.now() para comparación correcta
            if scheduled_datetime <= timezone.now():
                 raise serializers.ValidationError({"scheduled_datetime": "La fecha programada debe ser en el futuro."})
        elif scheduled_datetime and not is_scheduled:
             # Solo lanzar error si se proporciona fecha pero NO está marcado como programado
             # No lanzar error si NO se proporciona fecha Y NO está marcado como programado
            raise serializers.ValidationError({"is_scheduled": "Marque como 'pedido programado' si proporciona una fecha."})

        return data


class CreateOrderSerializer(serializers.Serializer):
    """Serializer para crear un pedido desde el carrito."""
    delivery_address = serializers.CharField(required=True, max_length=500)
    phone_number = serializers.CharField(required=True, max_length=20)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True) # Permitir null también
    is_scheduled = serializers.BooleanField(default=False)
    scheduled_datetime = serializers.DateTimeField(required=False, allow_null=True)

    def validate_scheduled_datetime(self, value):
         """Validación específica para la fecha programada."""
         # Se llama solo si 'scheduled_datetime' se proporciona en la data
         if value and value <= timezone.now() + timedelta(hours=1): # Añadir margen mínimo
             raise serializers.ValidationError(f"La fecha programada debe ser al menos una hora en el futuro.")
         return value

    def validate(self, data):
        """Validación general del serializer."""
        is_scheduled = data.get('is_scheduled', False)
        scheduled_datetime = data.get('scheduled_datetime')

        if is_scheduled and not scheduled_datetime:
            # Si está marcado como programado, la fecha es obligatoria (required=False la permite null)
             raise serializers.ValidationError({"scheduled_datetime": "Debe proporcionar una fecha y hora para pedidos programados."})
        elif scheduled_datetime and not is_scheduled:
             # Si se proporciona fecha pero no está marcado como programado
            raise serializers.ValidationError({"is_scheduled": "Marque como 'pedido programado' si proporciona una fecha."})

        # Validar que el carrito no esté vacío (contexto debe pasarse desde la vista)
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
             # Esto no debería pasar si la vista requiere autenticación
             raise serializers.ValidationError("Error interno: No se pudo determinar el usuario.")

        user = request.user
        try:
            # Usar select_related para optimizar un poco si accedes a campos del producto aquí
            cart = Cart.objects.prefetch_related('items__product').get(user=user)
            if not cart.items.exists():
                 raise serializers.ValidationError({"cart": "El carrito está vacío. Añade productos antes de crear un pedido."}) # Error a nivel de carrito
        except Cart.DoesNotExist:
             raise serializers.ValidationError({"cart": "No se encontró un carrito activo para este usuario."})

        return data

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Para que admin/staff actualicen el estado del pedido."""
    class Meta:
        model = Order
        fields = ['status'] # Solo permitir actualizar el estado
        # Podrías añadir validación de transición de estados aquí si fuera necesario


class AssignDelivererSerializer(serializers.ModelSerializer):
    """Para asignar un repartidor a un pedido."""
    # Usar assigned_to directamente y filtrar en la vista o con queryset
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_deliverer=True, is_active=True),
        allow_null=True, # Permitir desasignar pasando null
        required=False # No siempre se envía este campo
    )

    class Meta:
        model = Order
        fields = ['assigned_to']

    def validate_assigned_to(self, value):
        """Valida el repartidor asignado."""
        # 'value' es el objeto User (o None) seleccionado.
        # 'self.instance' es el objeto Order que se está actualizando.
        order = self.instance
        if not order:
            # No debería ocurrir en una actualización, pero por si acaso
            return value

        # Validar que el pedido esté en un estado asignable
        # Ajusta los estados permitidos según tu flujo
        allowed_statuses = ['PROCESSING', 'SCHEDULED']
        if order.status not in allowed_statuses:
             raise serializers.ValidationError(
                 f"No se puede asignar repartidor a un pedido en estado '{order.get_status_display()}'. "
                 f"Debe estar en estado: {', '.join(allowed_statuses)}."
            )

        # Si se está asignando (value no es None), asegúrate que sea un repartidor activo
        if value and (not value.is_deliverer or not value.is_active):
             raise serializers.ValidationError("El usuario seleccionado no es un repartidor activo.")

        return value