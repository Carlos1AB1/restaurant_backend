from rest_framework import serializers

class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False, max_length=1000)
    # Opcional: podrías pasar un ID de sesión o conversación
    # session_id = serializers.CharField(required=False, allow_blank=True)

class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    # Opcional: devolver el ID de sesión
    # session_id = serializers.CharField()