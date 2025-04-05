from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid
import datetime
from decimal import Decimal
from django.core.validators import MinValueValidator


class Cart(models.Model):
    """
    Modelo para el carrito de compras del usuario.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('usuario')
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('carrito')
        verbose_name_plural = _('carritos')

    def __str__(self):
        return f"Carrito de {self.user.username}"

    @property
    def total_items(self):
        """Retorna el número total de items en el carrito."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Retorna el subtotal del carrito (sin impuestos ni descuentos)."""
        return sum(item.line_total for item in self.items.all())

    @property
    def taxes(self):
        """Retorna el impuesto calculado sobre el subtotal."""
        tax_rate = Decimal('0.16')  # 16% de IVA
        return self.subtotal * tax_rate

    @property
    def total(self):
        """Retorna el total del carrito (subtotal + impuestos)."""
        return self.subtotal + self.taxes

    def clear(self):
        """Elimina todos los items del carrito."""
        self.items.all().delete()
        self.save()


class CartItem(models.Model):
    """
    Modelo para items dentro del carrito de compras.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('carrito')
    )
    dish = models.ForeignKey(
        'menu.Dish',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('plato')
    )
    quantity = models.PositiveIntegerField(
        _('cantidad'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField(_('notas adicionales'), blank=True)
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('ítem de carrito')
        verbose_name_plural = _('ítems de carrito')
        unique_together = ['cart', 'dish']

    def __str__(self):
        return f"{self.quantity} x {self.dish.name} ({self.cart.user.username})"

    @property
    def unit_price(self):
        """Retorna el precio unitario del plato (considerando promociones)."""
        return self.dish.final_price

    @property
    def line_total(self):
        """Retorna el precio total para este item (cantidad * precio unitario)."""
        return self.quantity * self.unit_price


class CartItemCustomization(models.Model):
    """
    Modelo para personalizaciones de items del carrito.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name='customizations',
        verbose_name=_('ítem de carrito')
    )
    dish_ingredient = models.ForeignKey(
        'menu.DishIngredient',
        on_delete=models.CASCADE,
        related_name='customizations',
        verbose_name=_('ingrediente del plato')
    )
    include = models.BooleanField(
        _('incluir'),
        default=True,
        help_text=_('Indica si se debe incluir o excluir este ingrediente')
    )
    extra = models.BooleanField(
        _('extra'),
        default=False,
        help_text=_('Indica si se debe agregar extra de este ingrediente')
    )

    class Meta:
        verbose_name = _('personalización de ítem')
        verbose_name_plural = _('personalizaciones de ítems')
        unique_together = ['cart_item', 'dish_ingredient']

    def __str__(self):
        action = "Incluir" if self.include else "Excluir"
        extra = " (Extra)" if self.extra else ""
        return f"{action}{extra} {self.dish_ingredient.ingredient.name} en {self.cart_item.dish.name}"


class Order(models.Model):
    """
    Modelo para pedidos del restaurante.
    """
    STATUS_CHOICES = (
        ('PENDING', _('Pendiente')),
        ('CONFIRMED', _('Confirmado')),
        ('PREPARING', _('En preparación')),
        ('READY', _('Listo para entrega')),
        ('OUT_FOR_DELIVERY', _('En camino')),
        ('DELIVERED', _('Entregado')),
        ('COMPLETED', _('Completado')),
        ('CANCELLED', _('Cancelado')),
    )

    DELIVERY_METHODS = (
        ('PICKUP', _('Recoger en restaurante')),
        ('DELIVERY', _('Entrega a domicilio')),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order_number = models.CharField(
        _('número de pedido'),
        max_length=20,
        unique=True,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('usuario')
    )
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    delivery_method = models.CharField(
        _('método de entrega'),
        max_length=20,
        choices=DELIVERY_METHODS,
        default='PICKUP'
    )
    delivery_address = models.ForeignKey(
        'users.Address',
        on_delete=models.SET_NULL,
        related_name='orders',
        verbose_name=_('dirección de entrega'),
        null=True,
        blank=True
    )
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tax = models.DecimalField(
        _('impuesto'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    delivery_fee = models.DecimalField(
        _('costo de entrega'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(_('notas adicionales'), blank=True)
    expected_delivery_time = models.DateTimeField(
        _('tiempo estimado de entrega'),
        null=True,
        blank=True
    )
    payment_id = models.CharField(_('ID de pago'), max_length=100, blank=True)
    payment_status = models.CharField(_('estado de pago'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('pedido')
        verbose_name_plural = _('pedidos')
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        # Generar número de pedido automáticamente si es nuevo
        if not self.order_number:
            today = datetime.date.today()
            prefix = today.strftime('%Y%m%d')

            # Contar pedidos del día para generar número secuencial
            day_orders_count = Order.objects.filter(
                created_at__date=today
            ).count()

            self.order_number = f"{prefix}-{day_orders_count + 1:04d}"

        # Calcular total si no se ha establecido
        if not self.total:
            self.total = self.subtotal + self.tax + self.delivery_fee

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Modelo para ítems dentro de un pedido.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('pedido')
    )
    dish = models.ForeignKey(
        'menu.Dish',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('plato')
    )
    dish_name = models.CharField(_('nombre del plato'), max_length=200)
    quantity = models.PositiveIntegerField(
        _('cantidad'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        _('precio unitario'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        _('precio total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(_('notas adicionales'), blank=True)

    class Meta:
        verbose_name = _('ítem de pedido')
        verbose_name_plural = _('ítems de pedido')

    def __str__(self):
        return f"{self.quantity} x {self.dish_name} (Pedido #{self.order.order_number})"

    def save(self, *args, **kwargs):
        # Guardar el nombre del plato en el momento de la orden
        if not self.dish_name:
            self.dish_name = self.dish.name

        # Calcular precio total
        self.total_price = self.quantity * self.unit_price

        super().save(*args, **kwargs)


class OrderItemCustomization(models.Model):
    """
    Modelo para personalizaciones de ítems de pedido.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='customizations',
        verbose_name=_('ítem de pedido')
    )
    ingredient_name = models.CharField(_('nombre del ingrediente'), max_length=100)
    include = models.BooleanField(_('incluir'), default=True)
    extra = models.BooleanField(_('extra'), default=False)
    extra_price = models.DecimalField(
        _('precio extra'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _('personalización de ítem de pedido')
        verbose_name_plural = _('personalizaciones de ítems de pedido')

    def __str__(self):
        action = "Incluir" if self.include else "Excluir"
        extra = " (Extra)" if self.extra else ""
        return f"{action}{extra} {self.ingredient_name} en {self.order_item.dish_name}"


class OrderStatusHistory(models.Model):
    """
    Modelo para registrar cambios de estado en los pedidos.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('pedido')
    )
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Order.STATUS_CHOICES
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    notes = models.TextField(_('notas'), blank=True)

    class Meta:
        verbose_name = _('historial de estado de pedido')
        verbose_name_plural = _('historial de estados de pedidos')
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.order.order_number} - {self.get_status_display()} ({self.created_at})"