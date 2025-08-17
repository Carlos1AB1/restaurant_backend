from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny # O IsAuthenticated si requiere login
from .serializers import ChatInputSerializer, ChatResponseSerializer
import random # Para respuestas de ejemplo

# --- Placeholder para la Lógica del Chatbot ---
# En un caso real, importarías tu librería/SDK de IA aquí
# from some_ai_library import get_ai_response

def get_placeholder_ai_response(message):
    """
    Función de placeholder que simula una respuesta de IA.
    ¡REEMPLAZAR CON LA INTEGRACIÓN REAL!
    """
    message_lower = message.lower()
    if "hola" in message_lower or "buenos días" in message_lower:
        return "¡Hola! ¿En qué puedo ayudarte hoy con nuestro menú o pedidos?"
    elif "menú" in message_lower or "comida" in message_lower or "platos" in message_lower:
        return "Puedes consultar nuestro menú completo en la sección 'Menú'. Tenemos hamburguesas, pizzas, ensaladas y más. ¿Te interesa alguna categoría en particular?"
    elif "horario" in message_lower:
        return "Nuestro horario de atención es de Lunes a Domingo, de 12:00 PM a 11:00 PM."
    elif "pedido" in message_lower or "orden" in message_lower:
        return "Puedes realizar tu pedido directamente desde nuestra web. Si tienes un número de pedido, puedo intentar buscar su estado (función no implementada aún)."
    elif "promocion" in message_lower or "oferta" in message_lower:
        return "Actualmente tenemos una promoción de 2x1 en pizzas medianas los martes. ¡Consulta la sección de promociones!"
    elif "gracias" in message_lower:
        return "¡De nada! Si necesitas algo más, no dudes en preguntar."
    else:
        # Respuesta genérica
        responses = [
            "Entendido. ¿Hay algo más en lo que pueda ayudarte?",
            "Gracias por tu consulta. ¿Necesitas más información?",
            "Estoy aquí para ayudar. ¿Tienes otra pregunta?",
            "No estoy seguro de cómo responder a eso. ¿Podrías reformular tu pregunta?",
        ]
        return random.choice(responses)
# --- Fin Placeholder ---


class ChatbotView(APIView):
    """
    Endpoint para interactuar con el chatbot de IA.
    """
    permission_classes = [AllowAny] # O IsAuthenticated

    def post(self, request, *args, **kwargs):
        input_serializer = ChatInputSerializer(data=request.data)
        if input_serializer.is_valid():
            message = input_serializer.validated_data['message']

            # --- Aquí iría la llamada a tu servicio/modelo de IA real ---
            # reply_text = get_ai_response(message, session_id=...)
            reply_text = get_placeholder_ai_response(message)
            # --- Fin llamada IA ---

            output_serializer = ChatResponseSerializer(data={'reply': reply_text})
            output_serializer.is_valid(raise_exception=True) # Debería ser siempre válido
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)