# restaurant_backend/apps/orders/permissions.py

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model() # Obtener el modelo User activo

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo al dueño del objeto
    (basado en el campo 'user') o a un usuario administrador (is_staff).
    Se usa para vistas de detalle o acciones sobre un objeto específico (Pedido, Carrito).
    """
    message = "No tienes permiso para realizar esta acción sobre este objeto."

    def has_object_permission(self, request, view, obj):
        # Asumimos que SAFE_METHODS (GET, HEAD, OPTIONS) podrían tener otros permisos
        # (como IsAuthenticatedOrReadOnly), este permiso se enfoca en escritura/modificación.
        # O puedes incluir la lógica de lectura aquí si es necesario.

        # Los administradores (staff) siempre tienen permiso para cualquier objeto.
        if request.user and request.user.is_staff:
            return True

        # Comprobar si el objeto tiene un campo 'user' (como Order o Cart)
        # y si ese campo coincide con el usuario que realiza la solicitud.
        if hasattr(obj, 'user'):
            # Asegurarse de que el usuario del objeto no sea None y coincida
            return obj.user and obj.user == request.user

        # Si el objeto no tiene campo 'user' o no coincide, denegar permiso.
        return False


class IsAdminOrDeliverer(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso a administradores (is_staff)
    o a usuarios marcados como repartidores (is_deliverer).
    Útil para vistas de lista o acciones generales no ligadas a UN objeto específico.
    """
    message = "Debes ser un administrador o repartidor para acceder a este recurso."

    def has_permission(self, request, view):
        # Primero, el usuario debe estar autenticado para ser admin o repartidor.
        if not request.user or not request.user.is_authenticated:
            return False

        # Comprobar si el usuario es staff.
        if request.user.is_staff:
            return True

        # Comprobar si el usuario tiene el atributo 'is_deliverer' y es True.
        # Usamos getattr para evitar errores si el campo no existe en algún modelo User antiguo/personalizado.
        # ¡ASEGÚRATE de que tu modelo User (apps/users/models.py) tiene el campo `is_deliverer = models.BooleanField(...)`!
        is_deliverer = getattr(request.user, 'is_deliverer', False)
        return is_deliverer


class IsAssignedDelivererOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo al repartidor
    ASIGNADO al objeto específico (pedido) o a un usuario administrador (is_staff).
    Se usa para acciones sobre un objeto específico, como 'mark_as_delivered'.
    """
    message = "Debes ser el repartidor asignado a este pedido o un administrador."

    def has_object_permission(self, request, view, obj):
        # El usuario debe estar autenticado.
        if not request.user or not request.user.is_authenticated:
            return False

        # Los administradores siempre tienen permiso.
        if request.user.is_staff:
            return True

        # Comprobar si el usuario es un repartidor.
        is_deliverer = getattr(request.user, 'is_deliverer', False)
        if not is_deliverer:
            return False # Si no es repartidor (y no es admin), no puede estar asignado.

        # Comprobar si el objeto (asumimos que es un pedido - Order)
        # tiene un campo 'assigned_to' y si coincide con el usuario actual.
        if hasattr(obj, 'assigned_to'):
            # Permitir si el repartidor asignado al objeto es el usuario actual.
            return obj.assigned_to and obj.assigned_to == request.user

        # Si el objeto no tiene 'assigned_to' o no coincide, denegar.
        return False