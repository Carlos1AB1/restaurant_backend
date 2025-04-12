from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product'] # Para buscar productos eficientemente
    extra = 0
    readonly_fields = ('get_item_total',)

    def get_item_total(self, obj):
        return obj.get_total_price()
    get_item_total.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'get_cart_total')
    list_filter = ('created_at',)
    search_fields = ('user__email',)
    inlines = [CartItemInline]
    readonly_fields = ('get_cart_total',)

    def get_cart_total(self, obj):
        return obj.get_total_price()
    get_cart_total.short_description = 'Total Carrito'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ('product_name', 'price', 'get_item_total')

    def get_item_total(self, obj):
        return obj.get_total_price()
    get_item_total.short_description = 'Subtotal'
    # Evitar que se puedan modificar los items una vez creado el pedido desde el admin
    can_delete = False
    # def has_add_permission(self, request, obj=None): return False
    # def has_change_permission(self, request, obj=None): return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user_email', 'status', 'total_price', 'is_scheduled',
        'scheduled_datetime', 'assigned_to_email', 'created_at'
    )
    list_filter = ('status', 'is_scheduled', 'created_at', 'scheduled_datetime')
    search_fields = ('order_number', 'user__email', 'delivery_address', 'phone_number', 'assigned_to__email')
    readonly_fields = ('order_number', 'user', 'total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    list_editable = ('status',) # Permitir cambiar estado desde la lista (cuidado!)
    fieldsets = (
        (None, {'fields': ('order_number', 'user', 'status', 'total_price')}),
        ('Detalles Entrega', {'fields': ('delivery_address', 'phone_number', 'notes')}),
        ('Programación', {'fields': ('is_scheduled', 'scheduled_datetime')}),
        ('Logística', {'fields': ('assigned_to',)}),
        ('Fechas', {'fields': ('created_at', 'updated_at')}),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'Cliente'

    def assigned_to_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else 'Sin asignar'
    assigned_to_email.short_description = 'Repartidor'

    # Filtrar el campo assigned_to para mostrar solo repartidores
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            kwargs["queryset"] = settings.AUTH_USER_MODEL.objects.filter(is_deliverer=True, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# No registrar CartItem y OrderItem directamente usualmente, se gestionan inline.
# admin.site.register(CartItem)
# admin.site.register(OrderItem)