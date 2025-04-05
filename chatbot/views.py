from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, Intent, RecommendationLog
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    ChatMessageRequestSerializer,
    IntentSerializer,
    RecommendationLogSerializer
)
from .services import ChatbotService


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para solo permitir administradores
    modificar objetos. Lectura permitida para todos.
    """

    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS para cualquier usuario
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permitir escritura solo a administradores
        return request.user and request.user.is_staff


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset para listar y obtener conversaciones.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna las conversaciones del usuario actual."""
        return Conversation.objects.filter(user=self.request.user)


class ChatMessageAPIView(APIView):
    """
    API para enviar mensajes al chatbot y recibir respuestas.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatMessageRequestSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            message_text = serializer.validated_data['message']
            conversation_id = serializer.validated_data.get('conversation_id')
            session_id = serializer.validated_data.get('session_id')

            # Obtener usuario autenticado o None
            user = request.user if request.user.is_authenticated else None

            try:
                # Obtener o crear conversación
                if conversation_id:
                    # Verificar que la conversación existe y pertenece al usuario
                    if user:
                        conversation = get_object_or_404(
                            Conversation, id=conversation_id, user=user
                        )
                    else:
                        conversation = get_object_or_404(
                            Conversation, id=conversation_id, session_id=session_id
                        )
                else:
                    # Crear o recuperar conversación basada en usuario o session_id
                    conversation = ChatbotService.create_or_get_conversation(
                        user=user, session_id=session_id
                    )

                # Procesar mensaje y obtener respuesta
                bot_message = ChatbotService.process_message(conversation, message_text)

                # Retornar respuesta
                return Response({
                    'conversation_id': conversation.id,
                    'message': MessageSerializer(bot_message).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetConversationAPIView(APIView):
    """
    API para reiniciar una conversación.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get('conversation_id')

        if not conversation_id:
            return Response(
                {"detail": _("Se requiere un ID de conversación.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que la conversación existe y pertenece al usuario
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)

            # Desactivar conversación actual
            conversation.is_active = False
            conversation.save()

            # Crear nueva conversación
            new_conversation = ChatbotService.create_or_get_conversation(user=request.user)

            return Response({
                'conversation_id': new_conversation.id,
                'message': _("Conversación reiniciada. ¿En qué puedo ayudarte?")
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response(
                {"detail": _("Conversación no encontrada.")},
                status=status.HTTP_404_NOT_FOUND
            )


class IntentViewSet(viewsets.ModelViewSet):
    """
    Viewset para CRUD de intenciones.
    Solo accesible por administradores.
    """
    queryset = Intent.objects.all()
    serializer_class = IntentSerializer
    permission_classes = [permissions.IsAdminUser]


class RecommendationLogListView(generics.ListAPIView):
    """
    Vista para listar registros de recomendaciones.
    """
    serializer_class = RecommendationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna las recomendaciones del usuario actual."""
        return RecommendationLog.objects.filter(user=self.request.user)