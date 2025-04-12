# restaurant_backend/apps/contact/serializers.py

from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo ContactMessage.

    Se encarga de validar los datos entrantes del formulario de contacto
    y de convertir las instancias del modelo ContactMessage a JSON
    para la respuesta de la API (aunque en este caso, la vista
    CreateAPIView solo devuelve el objeto creado en la respuesta).
    """
    class Meta:
        model = ContactMessage
        # Define los campos del modelo que se incluirán en la serialización.
        # Estos campos deben coincidir con los campos que esperas recibir
        # del formulario de contacto en el frontend.
        fields = [
            'id',           # El ID se genera automáticamente (read-only).
            'name',         # Nombre del remitente (requerido).
            'email',        # Email del remitente (requerido, DRF valida formato).
            'subject',      # Asunto del mensaje (requerido).
            'message',      # Cuerpo del mensaje (requerido).
            'created_at',   # Fecha de creación (read-only, se añade automáticamente).
            'is_read',      # Estado de leído (read-only para el usuario, gestionado por admin).
        ]

        # Define explícitamente los campos que son de solo lectura.
        # Aunque 'id' y 'created_at' son inherentemente read-only por
        # cómo están definidos en el modelo, y 'is_read' no debería
        # ser establecido por el usuario, es buena práctica listarlos.
        read_only_fields = [
            'id',
            'created_at',
            'is_read'
        ]

        # Puedes añadir validaciones adicionales a nivel de serializador si es necesario,
        # aunque las validaciones básicas (requerido, tipo de dato, longitud máxima)
        # a menudo se infieren directamente de los campos del modelo.
        # Ejemplo:
        # extra_kwargs = {
        #     'message': {'min_length': 10, 'error_messages': {'min_length': 'El mensaje debe tener al menos 10 caracteres.'}}
        # }

    # No se necesitan métodos `create` o `update` personalizados aquí porque
    # la vista `ContactMessageCreateView` usa `generics.CreateAPIView`, que
    # maneja la creación del objeto usando el serializador por defecto.
    # La lógica para enviar el correo de notificación se encuentra en el método
    # `perform_create` de la vista, después de que el serializador haya validado
    # y guardado el objeto.