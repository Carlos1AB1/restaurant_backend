from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.menu.models import Product

class Cart(models.Model):
    """Carrito de compras asociado a un usuario."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.user.email}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    """Item individual dentro de un carrito."""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('cart', 'product') # No permitir el mismo producto dos veces en el mismo carrito
        ordering = ['product__name']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} en {self.cart}"

    def get_total_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    """Representa un pedido realizado por un usuario."""
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('SCHEDULED', 'Programado'),
        ('OUT_FOR_DELIVERY', 'En Reparto'),
        ('DELIVERED', 'Entregado'),
        ('CANCELLED', 'Cancelado'),
        ('FAILED', 'Fallido'), # Por si falla el pago u otro motivo
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders') # Null si el usuario se elimina
    order_number = models.CharField(max_length=30, unique=True, editable=False) # Número de pedido único
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campos para dirección de entrega (puedes normalizar esto en un modelo Address si es complejo)
    delivery_address = models.TextField(blank=True, null=True) # O campos separados: street, city, postal_code...
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Teléfono de contacto para la entrega

    # Campos para pedidos programados
    is_scheduled = models.BooleanField(default=False, verbose_name="Es Programado")
    scheduled_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Fecha y Hora Programada")

    # Para logística
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', limit_choices_to={'is_deliverer': True}, verbose_name="Repartidor Asignado")

    # Información adicional o notas del cliente
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at'] # Pedidos más recientes primero
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido {self.order_number} ({self.user.email if self.user else 'Usuario eliminado'})"

    def _generate_order_number(self):
        # Genera un número de pedido único basado en timestamp y UUID corto
        ts = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"ORD-{ts}-{unique_id}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
            # Asegurar unicidad (muy improbable colisión, pero por si acaso)
            while Order.objects.filter(order_number=self.order_number).exists():
                self.order_number = self._generate_order_number()

        # Validar fecha programada si aplica
        if self.is_scheduled and self.scheduled_datetime:
            if self.scheduled_datetime <= timezone.now():
                 raise ValueError("La fecha programada debe ser en el futuro.")
            if self.status == 'PENDING': # Cambiar estado si está programado
                self.status = 'SCHEDULED'
        elif self.is_scheduled and not self.scheduled_datetime:
             raise ValueError("Se debe especificar una fecha y hora para pedidos programados.")
        elif not self.is_scheduled:
            self.scheduled_datetime = None # Limpiar fecha si no es programado

        super().save(*args, **kwargs)

    def can_cancel(self):
        """Verifica si el pedido puede ser cancelado según el tiempo límite."""
        if self.status in ['DELIVERED', 'CANCELLED', 'OUT_FOR_DELIVERY']:
            return False # No se puede cancelar si ya fue entregado, cancelado o está en reparto

        # Pedidos programados: Se pueden cancelar antes de N horas de la fecha programada (ej. 24h)
        if self.is_scheduled and self.scheduled_datetime:
            # Definir el límite de cancelación para programados (ej. 24 horas antes)
            cancellation_deadline = self.scheduled_datetime - timedelta(hours=24)
            return timezone.now() < cancellation_deadline

        # Pedidos normales: Límite de tiempo desde la creación
        time_limit = timedelta(minutes=settings.ORDER_CANCELLATION_LIMIT_MINUTES)
        return (timezone.now() - self.created_at) < time_limit

class OrderItem(models.Model):
    """Item individual dentro de un pedido."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True) # Guardar referencia, pero permitir si el producto se borra
    product_name = models.CharField(max_length=200) # Guardar nombre por si el producto cambia/borra
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]) # Guardar precio por si cambia
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Pedido {self.order.order_number})"

    def get_total_price(self):
        return self.quantity * self.price

# Añadir campo is_deliverer al modelo User (ejecuta makemigrations y migrate después)
# Añade esto a tu apps/users/models.py y crea la migración:
# class User(...):
#     ...
#     is_deliverer = models.BooleanField(default=False, verbose_name="Es Repartidor")

# Asegúrate de añadir 'is_deliverer' a los serializers y admin si es necesario gestionarlo.