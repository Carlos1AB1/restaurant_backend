# restaurant_backend/apps/delivery/admin.py

from django.contrib import admin

# Register your models here.
# from .models import DelivererProfile # Ejemplo si tuvieras modelos aquí

# Nota: En la implementación actual, no hay modelos específicos en la app 'delivery'
# para registrar en el admin.
# - La gestión de qué usuarios son repartidores (campo 'is_deliverer') se hace
#   a través del admin de la app 'users' (modificando el modelo User).
# - La asignación de un repartidor a un pedido se hace a través del admin
#   de la app 'orders' (modificando el modelo Order).

# Ejemplo de cómo registrarías un modelo si lo tuvieras:
# @admin.register(DelivererProfile)
# class DelivererProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'vehicle_type', 'is_available')
#     list_filter = ('vehicle_type', 'is_available')
#     search_fields = ('user__email', 'user__first_name', 'user__last_name')
#     raw_id_fields = ('user',) # Para búsqueda eficiente de usuarios