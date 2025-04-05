from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import (
    Cart, CartItem, CartItemCustomization,
    Order, OrderItem, OrderItemCustomization, OrderStatusHistory
)
from menu.models import Dish, DishIngredient
from users.models import Address
from menu.serializers import DishListSerializer
from notifications.services import send_order_confirmation_email


class CartItemCustomizationSerializer(serializers.ModelSerializer):
    """Serializer para personalizaciones de ítems de carrito."""

    ingredient_name = serializers.CharField(source='dish_ingredient.ingredient.name', read_only=True)

    class Meta:
        model = CartItemCustomization
        fields = ['id', 'dish_ingredient', 'ingredient_name', 'include', 'extra']
        extra_kwargs = {
            'dish_ingredient': {'write_only': True}
        }


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer para ítems de carrito."""

    dish_details = DishListSerializer(source='dish', read_only=True)
    customizations = CartItemCustomizationSerializer(many=True, required=False)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'dish', 'dish_details', 'quantity', 'notes',
            'customizations', 'unit_price', 'line_total'
        ]
        extra_kwargs = {
            'dish': {'write_only': True}
        }

    def validate_dish(self, value):
        """Validar que el plato esté activo."""
        if not value.is_active:
            raise serializers.ValidationError(_("Este plato no está disponible actualmente."))
        return value

    def create(self, validated_data):
        customizations_data = validated_data.pop('customizations', [])

        # Obtener o crear carrito para el usuario actual
        user = self.context['request'].user
        cart, created = Cart.objects.get_or_create(user=user)

        # Verificar si ya existe un item con este plato en el carrito
        try:
            cart_item = CartItem.objects.get(cart=cart, dish=validated_data['dish'])
            # Actualizar cantidad si ya existe
            cart_item.quantity += validated_data.get('quantity', 1)
            cart_item.notes = validated_data.get('notes', cart_item.notes)
            cart_item.save()
        except CartItem.DoesNotExist:
            # Crear nuevo item
            cart_item = CartItem.objects.create(cart=cart, **validated_data)

        # Procesar personalizaciones
        self._process_customizations(cart_item, customizations_data)

        return cart_item

    def update(self, instance, validated_data):
        customizations_data = validated_data.pop('customizations', None)

        # Actualizar campos del item
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar personalizaciones si se proporcionaron
        if customizations_data is not None:
            # Eliminar personalizaciones anteriores
            instance.customizations.all().delete()
            # Crear nuevas personalizaciones
            self._process_customizations(instance, customizations_data)

        return instance

    def _process_customizations(self, cart_item, customizations_data):
        """Helper para procesar personalizaciones de un ítem de carrito."""
        for customization_data in customizations_data:
            CartItemCustomization.objects.create(
                cart_item=cart_item,
                **customization_data
            )


class CartSerializer(serializers.ModelSerializer):
    """Serializer para carrito de compras."""

    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    taxes = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'subtotal', 'taxes', 'total', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class OrderItemCustomizationSerializer(serializers.ModelSerializer):
    """Serializer para personalizaciones de ítems de pedido."""

    class Meta:
        model = OrderItemCustomization
        fields = ['id', 'ingredient_name', 'include', 'extra', 'extra_price']
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para ítems de pedido."""

    customizations = OrderItemCustomizationSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'dish', 'dish_name', 'quantity', 'unit_price',
            'total_price', 'notes', 'customizations'
        ]
        read_only_fields = fields


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer para historial de estados de pedido."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'created_at', 'notes']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serializer para pedidos."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_email', 'status', 'status_display',
            'delivery_method', 'delivery_method_display', 'delivery_address',
            'subtotal', 'tax', 'delivery_fee', 'total', 'notes',
            'expected_delivery_time', 'payment_id', 'payment_status',
            'items', 'status_history', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'user_email', 'subtotal', 'tax',
            'total', 'payment_id', 'payment_status', 'items', 'status_history',
            'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pedidos a partir del carrito."""

    delivery_address_id = serializers.UUIDField(required=False)

    class Meta:
        model = Order
        fields = ['delivery_method', 'delivery_address_id', 'notes']

    def validate(self, attrs):
        # Validar que si el método es entrega, se proporcione una dirección
        if attrs.get('delivery_method') == 'DELIVERY' and not attrs.get('delivery_address_id'):
            raise serializers.ValidationError({
                "delivery_address_id": _("Se requiere una dirección de entrega para el método de entrega seleccionado.")
            })

        # Validar que el carrito no esté vacío
        user = self.context['request'].user
        try:
            cart = Cart.objects.get(user=user)
            if cart.items.count() == 0:
                raise serializers.ValidationError(_("El carrito está vacío. Agrega platos antes de crear un pedido."))
        except Cart.DoesNotExist:
            raise serializers.ValidationError(_("El carrito no existe. Agrega platos antes de crear un pedido."))

        return attrs

    def validate_delivery_address_id(self, value):
        """Validar que la dirección pertenezca al usuario."""
        if value:
            user = self.context['request'].user
            try:
                address = Address.objects.get(id=value, user=user)
                return address
            except Address.DoesNotExist:
                raise serializers.ValidationError(_("La dirección seleccionada no existe o no pertenece al usuario."))
        return None

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.get(user=user)

        # Extraer dirección si existe
        address = validated_data.pop('delivery_address_id', None)

        # Calcular subtotal, impuestos y total
        subtotal = cart.subtotal
        tax = cart.taxes
        delivery_fee = Decimal('0.00')

        # Aplicar tarifa de entrega si es a domicilio
        if validated_data.get('delivery_method') == 'DELIVERY':
            delivery_fee = Decimal('50.00')  # Tarifa fija de entrega

        total = subtotal + tax + delivery_fee

        # Calcular tiempo estimado de entrega
        expected_delivery_time = None
        if validated_data.get('delivery_method') == 'PICKUP':
            # 30 minutos para recoger
            expected_delivery_time = timezone.now() + timedelta(minutes=30)
        else:
            # 60 minutos para entrega a domicilio
            expected_delivery_time = timezone.now() + timedelta(minutes=60)

        # Crear orden
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            total=total,
            delivery_address=address,
            expected_delivery_time=expected_delivery_time,
            **validated_data
        )

        # Crear historial de estado inicial
        OrderStatusHistory.objects.create(
            order=order,
            status='PENDING',
            notes=_("Pedido creado")
        )

        # Transferir items del carrito a la orden
        for cart_item in cart.items.all():
            # Crear item de pedido
            order_item = OrderItem.objects.create(
                order=order,
                dish=cart_item.dish,
                dish_name=cart_item.dish.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.line_total,
                notes=cart_item.notes
            )

            # Transferir personalizaciones
            for customization in cart_item.customizations.all():
                OrderItemCustomization.objects.create(
                    order_item=order_item,
                    ingredient_name=customization.dish_ingredient.ingredient.name,
                    include=customization.include,
                    extra=customization.extra,
                    extra_price=customization.dish_ingredient.extra_price if customization.extra else Decimal('0.00')
                )

        # Vaciar carrito
        cart.clear()

        # Enviar email de confirmación
        send_order_confirmation_email(order)

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar el estado de un pedido."""

    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        notes = validated_data.get('notes', '')

        # Actualizar estado del pedido
        instance.status = new_status
        instance.save()

        # Registrar cambio en historial
        OrderStatusHistory.objects.create(
            order=instance,
            status=new_status,
            notes=notes
        )

        # Enviar notificación de actualización de estado
        from notifications.services import send_order_status_update_email
        send_order_status_update_email(instance)

        return instance