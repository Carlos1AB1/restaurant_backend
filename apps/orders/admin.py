# apps/orders/admin.py

from django.contrib import admin
from django.conf import settings  # <--- IMPORTACIÓN AÑADIDA
from django.contrib.auth import get_user_model # <--- IMPORTACIÓN AÑADIDA para mejor práctica

from .models import Cart, CartItem, Order, OrderItem

# Obtener el modelo de Usuario activo (mejor práctica que settings.AUTH_USER_MODEL directamente)
User = get_user_model()

class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product'] # Para buscar productos eficientemente
    extra = 0
    readonly_fields = ('get_item_total',)
    # Opcional: Añadir campos si quieres ver más info del producto aquí
    # fields = ('product', 'quantity', 'get_item_total')

    def get_item_total(self, obj):
        # Asegurarse que get_total_price existe y maneja errores si es necesario
        try:
            return obj.get_total_price()
        except Exception as e:
            print(f"Error calculating CartItem total: {e}") # Log de error
            return "Error"
    get_item_total.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'get_cart_total') # Añadir 'id' suele ser útil
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'id') # Buscar por ID, email o username
    inlines = [CartItemInline]
    readonly_fields = ('get_cart_total', 'created_at', 'updated_at') # Hacer fechas readonly también
    date_hierarchy = 'created_at' # Navegación por fechas

    def get_cart_total(self, obj):
         # Asegurarse que get_total_price existe y maneja errores si es necesario
        try:
            # Considerar formatear el precio aquí si es necesario (ej: con f-string)
            return obj.get_total_price()
        except Exception as e:
            print(f"Error calculating Cart total: {e}") # Log de error
            return "Error"
    get_cart_total.short_description = 'Total Carrito'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    # Mostrar campos relevantes y permitir ver el subtotal
    fields = ('product', 'product_name', 'price', 'quantity', 'get_item_total')
    readonly_fields = ('product_name', 'price', 'get_item_total') # Mantener precio histórico y subtotal
    # Permitir edición de cantidad si tiene sentido para tu flujo
    # readonly_fields = ('product_name', 'price', 'quantity', 'get_item_total')

    def get_item_total(self, obj):
         # Asegurarse que get_total_price existe y maneja errores si es necesario
        try:
            # Considerar formatear el precio aquí si es necesario
            return obj.get_total_price()
        except Exception as e:
            print(f"Error calculating OrderItem total: {e}") # Log de error
            return "Error"
    get_item_total.short_description = 'Subtotal'

    # Prevenir añadir o borrar items desde un pedido existente podría ser buena idea
    can_delete = False
    # def has_add_permission(self, request, obj=None): return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'user_email',
        'status',
        'total_price_display',
        'is_scheduled',
        'scheduled_datetime',
        'assigned_to_email', # Muestra el email del repartidor (método)
        'assigned_to',      # <-- ¡AÑADIDO! El campo base necesario para list_editable
        'created_at'
    )
    list_filter = ('status', 'is_scheduled', 'created_at', 'scheduled_datetime', 'assigned_to')
    search_fields = ('order_number', 'user__email', 'delivery_address', 'phone_number', 'assigned_to__email', 'user__username')
    readonly_fields = ('order_number', 'user', 'total_price', 'created_at', 'updated_at', 'total_price_display')
    inlines = [OrderItemInline]
    # Ahora 'assigned_to' está en list_display, por lo que puede estar en list_editable
    list_editable = ('status', 'assigned_to')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('order_number', 'user', 'status', 'total_price_display')}),
        ('Detalles Cliente y Entrega', {'fields': ('delivery_address', 'phone_number', 'notes')}),
        ('Programación', {'fields': ('is_scheduled', 'scheduled_datetime'), 'classes': ('collapse',)}),
        ('Logística', {'fields': ('assigned_to',)}), # 'assigned_to' ya estaba aquí, correcto
        ('Fechas Importantes', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    # --- Métodos (sin cambios necesarios aquí para este error) ---
    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'Cliente'
    user_email.admin_order_field = 'user__email'

    def assigned_to_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else 'Sin asignar'
    assigned_to_email.short_description = 'Repartidor (Email)' # Cambié descripción para diferenciar
    assigned_to_email.admin_order_field = 'assigned_to__email'

    def total_price_display(self, obj):
        try:
            return f"{obj.total_price:.2f} €"
        except (TypeError, ValueError, AttributeError):
             return obj.total_price
    total_price_display.short_description = 'Total (€)'
    total_price_display.admin_order_field = 'total_price'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "assigned_to":
            try:
                kwargs["queryset"] = User.objects.filter(is_deliverer=True, is_active=True)
            except AttributeError:
                 print("Advertencia: El modelo User no tiene el campo 'is_deliverer'.")
            except Exception as e:
                 print(f"Error al filtrar queryset para 'assigned_to': {e}")
        return kwargs