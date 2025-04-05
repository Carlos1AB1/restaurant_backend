from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message, Intent, RecommendationLog
from menu.serializers import DishListSerializer


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer para mensajes de chatbot.
    """
    sender_display = serializers.CharField(source='get_sender_display', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_display', 'content', 'created_at']
        read_only_fields = ['id', 'sender_display', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer para conversaciones de chatbot.
    """
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatMessageRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitudes de mensaje al chatbot.
    """
    message = serializers.CharField(required=True)
    conversation_id = serializers.UUIDField(required=False)
    session_id = serializers.CharField(required=False, max_length=100)

    def validate(self, attrs):
        """
        Validar que se proporcione conversation_id o session_id.
        """
        # Si el usuario está autenticado, no es necesario session_id
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return attrs

        # Si no está autenticado, validar que se proporcione session_id
        if not attrs.get('session_id'):
            raise serializers.ValidationError({
                "session_id": _("Se requiere un ID de sesión para usuarios no autenticados.")
            })

        return attrs


class IntentSerializer(serializers.ModelSerializer):
    """
    Serializer para intenciones del chatbot.
    """

    class Meta:
        model = Intent
        fields = [
            'id', 'name', 'description', 'examples',
            'response_template', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecommendationLogSerializer(serializers.ModelSerializer):
    """
    Serializer para registros de recomendaciones.
    """
    dish_details = DishListSerializer(source='dish', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RecommendationLog
        fields = [
            'id', 'user', 'user_username', 'session_id',
            'dish', 'dish_details', 'context', 'created_at'
        ]
        read_only_fields = ['id', 'user_username', 'created_at']