import json
import logging
import random
import requests
from django.conf import settings
from django.db.models import Count, Avg, Q
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message, Intent, RecommendationLog
from menu.models import Dish, Category

# Configurar logger
logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Servicio para manejar la lógica del chatbot.
    """

    @staticmethod
    def create_or_get_conversation(user=None, session_id=None):
        """
        Crea o recupera una conversación activa.

        Args:
            user: Usuario autenticado (opcional)
            session_id: ID de sesión para usuarios no autenticados (opcional)

        Returns:
            Conversation: Instancia de Conversación
        """
        if user:
            # Buscar conversación activa del usuario
            conversation = Conversation.objects.filter(
                user=user,
                is_active=True
            ).first()

            # Crear nueva si no existe
            if not conversation:
                conversation = Conversation.objects.create(user=user)

                # Mensaje de bienvenida automático
                Message.objects.create(
                    conversation=conversation,
                    sender='BOT',
                    content=_("¡Hola! Soy el asistente virtual del restaurante. ¿En qué puedo ayudarte hoy?")
                )

            return conversation

        elif session_id:
            # Buscar conversación activa por session_id
            conversation = Conversation.objects.filter(
                session_id=session_id,
                is_active=True
            ).first()

            # Crear nueva si no existe
            if not conversation:
                conversation = Conversation.objects.create(session_id=session_id)

                # Mensaje de bienvenida automático
                Message.objects.create(
                    conversation=conversation,
                    sender='BOT',
                    content=_("¡Hola! Soy el asistente virtual del restaurante. ¿En qué puedo ayudarte hoy?")
                )

            return conversation

        else:
            raise ValueError(_("Se requiere usuario o ID de sesión"))

    @staticmethod
    def process_message(conversation, message_text):
        """
        Procesa un mensaje del usuario y genera una respuesta.

        Args:
            conversation: Instancia de Conversation
            message_text: Texto del mensaje del usuario

        Returns:
            Message: Instancia del mensaje de respuesta del bot
        """
        # Registrar mensaje del usuario
        user_message = Message.objects.create(
            conversation=conversation,
            sender='USER',
            content=message_text
        )

        # Detectar intención del mensaje
        intent_data = ChatbotService.detect_intent(message_text)
        intent_name = intent_data.get('intent', 'fallback')
        entities = intent_data.get('entities', [])

        # Generar respuesta basada en la intención
        if intent_name == 'greeting':
            response_text = ChatbotService.handle_greeting(conversation)
        elif intent_name == 'menu_inquiry':
            response_text = ChatbotService.handle_menu_inquiry(entities)
        elif intent_name == 'dish_recommendation':
            response_text = ChatbotService.handle_dish_recommendation(
                conversation, entities, user_message
            )
        elif intent_name == 'order_status':
            response_text = ChatbotService.handle_order_status(conversation)
        elif intent_name == 'opening_hours':
            response_text = ChatbotService.handle_opening_hours()
        elif intent_name == 'location':
            response_text = ChatbotService.handle_location()
        elif intent_name == 'add_to_cart':
            response_text = ChatbotService.handle_add_to_cart(conversation, entities)
        else:
            # Intención no reconocida
            response_text = _("Lo siento, no he entendido tu consulta. ¿Puedes reformularla?")

        # Registrar respuesta del bot
        bot_message = Message.objects.create(
            conversation=conversation,
            sender='BOT',
            content=response_text
        )

        # Actualizar timestamp de la conversación
        conversation.save()

        return bot_message

    @staticmethod
    def detect_intent(message_text):
        """
        Detecta la intención del mensaje del usuario.

        Args:
            message_text: Texto del mensaje

        Returns:
            dict: Información de la intención detectada
        """
        try:
            # Intentar usar el servicio Rasa si está configurado
            if hasattr(settings, 'RASA_NLU_ENDPOINT') and settings.RASA_NLU_ENDPOINT:
                response = requests.post(
                    settings.RASA_NLU_ENDPOINT,
                    json={"text": message_text}
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        'intent': data.get('intent', {}).get('name', 'fallback'),
                        'confidence': data.get('intent', {}).get('confidence', 0),
                        'entities': data.get('entities', [])
                    }

            # Fallback: Lógica simple basada en palabras clave
            logger.warning("Usando detección de intención fallback basada en palabras clave")

            # Convertir a minúsculas para búsquedas no sensibles a mayúsculas
            message_lower = message_text.lower()

            # Palabras clave para cada intención
            intent_keywords = {
                'greeting': ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos'],
                'menu_inquiry': ['menú', 'carta', 'platos', 'comidas', 'bebidas', 'qué ofrecen'],
                'dish_recommendation': ['recomienda', 'sugerencia', 'qué me recomiendas', 'plato popular'],
                'order_status': ['estado', 'pedido', 'mi orden', 'seguimiento'],
                'opening_hours': ['horario', 'hora', 'abierto', 'cierran', 'abren'],
                'location': ['ubicación', 'dirección', 'dónde están', 'cómo llego'],
                'add_to_cart': ['agregar', 'añadir', 'carrito', 'pedir', 'comprar']
            }

            # Buscar coincidencias
            max_matches = 0
            detected_intent = 'fallback'

            for intent, keywords in intent_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in message_lower)
                if matches > max_matches:
                    max_matches = matches
                    detected_intent = intent

            # Extraer entidades básicas (categorías y platos mencionados)
            entities = []

            # Buscar categorías mencionadas
            for category in Category.objects.filter(is_active=True):
                if category.name.lower() in message_lower:
                    entities.append({
                        'entity': 'category',
                        'value': category.name,
                        'id': str(category.id)
                    })

            # Buscar platos mencionados
            for dish in Dish.objects.filter(is_active=True):
                if dish.name.lower() in message_lower:
                    entities.append({
                        'entity': 'dish',
                        'value': dish.name,
                        'id': str(dish.id)
                    })

            return {
                'intent': detected_intent,
                'confidence': 0.6 if max_matches > 0 else 0.3,
                'entities': entities
            }

        except Exception as e:
            logger.error(f"Error al detectar intención: {str(e)}")
            return {
                'intent': 'fallback',
                'confidence': 0,
                'entities': []
            }

    @staticmethod
    def handle_greeting(conversation):
        """
        Maneja la intención de saludo.

        Args:
            conversation: Instancia de Conversation

        Returns:
            str: Texto de respuesta
        """
        # Personalizar saludo si conocemos al usuario
        if conversation.user:
            username = conversation.user.first_name or conversation.user.username
            greeting = _("¡Hola, {}! ").format(username)
        else:
            greeting = _("¡Hola! ")

        # Agregar opciones de ayuda
        return greeting + _(
            "Puedo ayudarte con información sobre nuestro menú, recomendaciones de platos, estado de tu pedido y más. ¿En qué puedo asistirte hoy?")

    @staticmethod
    def handle_menu_inquiry(entities):
        """
        Maneja la intención de consulta sobre el menú.

        Args:
            entities: Entidades detectadas en el mensaje

        Returns:
            str: Texto de respuesta
        """
        # Verificar si se menciona una categoría específica
        category_entities = [e for e in entities if e.get('entity') == 'category']

        if category_entities:
            # Consulta sobre categoría específica
            category_name = category_entities[0].get('value')
            category_id = category_entities[0].get('id')

            try:
                category = Category.objects.get(id=category_id)
                dishes = Dish.objects.filter(category=category, is_active=True)

                if dishes.exists():
                    dishes_text = ", ".join([f"{dish.name} (${dish.price})" for dish in dishes[:5]])

                    if dishes.count() > 5:
                        dishes_text += _(" y {} más").format(dishes.count() - 5)

                    return _(
                        "En nuestra categoría de {} tenemos: {}. ¿Te gustaría más información sobre algún plato en particular?").format(
                        category.name, dishes_text
                    )
                else:
                    return _(
                        "Actualmente no tenemos platos disponibles en la categoría {}. ¿Puedo mostrarte otras categorías?").format(
                        category.name)

            except Category.DoesNotExist:
                pass

        # Consulta general sobre el menú
        categories = Category.objects.filter(is_active=True)

        if categories.exists():
            categories_text = ", ".join([category.name for category in categories])
            return _("Nuestro menú incluye las siguientes categorías: {}. ¿Sobre cuál te gustaría saber más?").format(
                categories_text)
        else:
            return _(
                "Estamos actualizando nuestro menú. Por favor, consulta más tarde o pregunta por nuestras recomendaciones del día.")

    @staticmethod
    def handle_dish_recommendation(conversation, entities, message):
        """
        Maneja la intención de recomendación de platos.

        Args:
            conversation: Instancia de Conversation
            entities: Entidades detectadas en el mensaje
            message: Mensaje del usuario

        Returns:
            str: Texto de respuesta
        """
        # Verificar si se menciona una categoría específica
        category_entities = [e for e in entities if e.get('entity') == 'category']

        # Usuario autenticado o sesión
        user = conversation.user
        session_id = conversation.session_id

        if category_entities:
            # Recomendación para categoría específica
            category_id = category_entities[0].get('id')
            try:
                category = Category.objects.get(id=category_id)

                # Buscar platos destacados en esta categoría
                featured_dishes = Dish.objects.filter(
                    category=category,
                    is_active=True,
                    is_featured=True
                )

                if featured_dishes.exists():
                    # Seleccionar un plato destacado al azar
                    dish = random.choice(featured_dishes)
                else:
                    # Si no hay destacados, buscar platos con buenas reseñas
                    top_dishes = Dish.objects.filter(
                        category=category,
                        is_active=True
                    ).annotate(
                        avg_rating=Avg('reviews__rating')
                    ).filter(
                        avg_rating__gte=4  # Platos con al menos 4 estrellas
                    ).order_by('-avg_rating')

                    if top_dishes.exists():
                        dish = top_dishes.first()
                    else:
                        # Si no hay reseñas, seleccionar cualquier plato
                        dishes = Dish.objects.filter(category=category, is_active=True)
                        if dishes.exists():
                            dish = random.choice(dishes)
                        else:
                            return _(
                                "Lo siento, actualmente no tenemos platos disponibles en la categoría {}. ¿Puedo recomendarte algo de otra categoría?").format(
                                category.name)

                # Registrar recomendación
                RecommendationLog.objects.create(
                    user=user,
                    session_id=session_id,
                    message=message,
                    dish=dish,
                    context=f"Categoría: {category.name}"
                )

                return _("Te recomiendo '{0}'. {1}. Su precio es ${2}. ¿Te gustaría agregarlo a tu carrito?").format(
                    dish.name, dish.description, dish.price
                )

            except Category.DoesNotExist:
                pass

        # Recomendación general
        # Buscar platos populares o destacados
        popular_dishes = Dish.objects.filter(
            is_active=True
        ).annotate(
            order_count=Count('order_items')
        ).order_by('-order_count', '-is_featured')[:3]

        if popular_dishes.exists():
            dishes = list(popular_dishes)
            # Seleccionar uno al azar entre los más populares
            dish = random.choice(dishes)

            # Registrar recomendación
            RecommendationLog.objects.create(
                user=user,
                session_id=session_id,
                message=message,
                dish=dish,
                context="Recomendación general"
            )

            return _(
                "Uno de nuestros platos más populares es '{0}'. {1}. Su precio es ${2}. ¿Te gustaría agregarlo a tu carrito?").format(
                dish.name, dish.description, dish.price
            )
        else:
            return _(
                "Lo siento, no puedo hacer una recomendación en este momento. Por favor, consulta nuestro menú para ver las opciones disponibles.")

    @staticmethod
    def handle_order_status(conversation):
        """
        Maneja la intención de consulta sobre estado de pedido.

        Args:
            conversation: Instancia de Conversation

        Returns:
            str: Texto de respuesta
        """
        # Solo para usuarios autenticados
        if not conversation.user:
            return _(
                "Para consultar el estado de tu pedido, necesitas iniciar sesión. ¿Ya tienes una cuenta con nosotros?")

        # Buscar pedidos activos del usuario
        from orders.models import Order
        active_orders = Order.objects.filter(
            user=conversation.user,
            status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'OUT_FOR_DELIVERY']
        ).order_by('-created_at')

        if active_orders.exists():
            order = active_orders.first()
            status_display = order.get_status_display()

            if order.expected_delivery_time:
                from django.utils import timezone
                if order.expected_delivery_time > timezone.now():
                    time_str = order.expected_delivery_time.strftime("%H:%M")
                    return _(
                        "Tu pedido #{0} está {1}. Esperamos entregarlo alrededor de las {2}. ¿Necesitas algo más?").format(
                        order.order_number, status_display.lower(), time_str
                    )

            return _("Tu pedido #{0} está {1}. ¿Necesitas algo más?").format(
                order.order_number, status_display.lower()
            )
        else:
            # Buscar pedidos recientes finalizados
            recent_orders = Order.objects.filter(
                user=conversation.user,
                status__in=['DELIVERED', 'COMPLETED']
            ).order_by('-created_at')[:1]

            if recent_orders.exists():
                return _(
                    "No tienes pedidos activos en este momento. Tu último pedido ya fue entregado. ¿Te gustaría hacer un nuevo pedido?")
            else:
                return _("No encontramos pedidos asociados a tu cuenta. ¿Te gustaría realizar tu primer pedido?")

    @staticmethod
    def handle_opening_hours():
        """
        Maneja la intención de consulta sobre horarios.

        Returns:
            str: Texto de respuesta
        """
        # Horarios estáticos (idealmente, estos vendrían de la configuración)
        opening_hours = {
            'monday': {'open': '11:00', 'close': '22:00'},
            'tuesday': {'open': '11:00', 'close': '22:00'},
            'wednesday': {'open': '11:00', 'close': '22:00'},
            'thursday': {'open': '11:00', 'close': '22:00'},
            'friday': {'open': '11:00', 'close': '23:00'},
            'saturday': {'open': '10:00', 'close': '23:00'},
            'sunday': {'open': '10:00', 'close': '21:00'},
        }

        days_es = {
            'monday': _('lunes'),
            'tuesday': _('martes'),
            'wednesday': _('miércoles'),
            'thursday': _('jueves'),
            'friday': _('viernes'),
            'saturday': _('sábado'),
            'sunday': _('domingo'),
        }

        hours_text = ""
        for day, hours in opening_hours.items():
            hours_text += _("{}: {} a {}\n").format(
                days_es[day], hours['open'], hours['close']
            )

        return _("Nuestros horarios de atención son:\n\n{}").format(hours_text)

    @staticmethod
    def handle_location():
        """
        Maneja la intención de consulta sobre ubicación.

        Returns:
            str: Texto de respuesta
        """
        # Ubicación estática (idealmente, vendría de la configuración)
        address = "Av. Insurgentes Sur 1234, Col. Del Valle, Ciudad de México"
        reference = "Entre las calles Félix Cuevas y Tlacoquemécatl"

        return _("Estamos ubicados en: {}\n{}").format(address, reference)

    @staticmethod
    def handle_add_to_cart(conversation, entities):
        """
        Maneja la intención de agregar al carrito.

        Args:
            conversation: Instancia de Conversation
            entities: Entidades detectadas en el mensaje

        Returns:
            str: Texto de respuesta
        """
        # Solo para usuarios autenticados
        if not conversation.user:
            return _("Para agregar platos a tu carrito, necesitas iniciar sesión. ¿Ya tienes una cuenta con nosotros?")

        # Verificar si se menciona un plato específico
        dish_entities = [e for e in entities if e.get('entity') == 'dish']

        if dish_entities:
            # Agregar plato específico
            dish_id = dish_entities[0].get('id')
            try:
                dish = Dish.objects.get(id=dish_id)

                # Aquí deberíamos integrarnos con el sistema de carrito
                # Por ahora, solo simulamos la respuesta

                return _("He agregado '{}' a tu carrito. ¿Deseas agregar algo más o proceder al checkout?").format(
                    dish.name)

            except Dish.DoesNotExist:
                return _("Lo siento, no encontré ese plato en nuestro menú. ¿Puedo recomendarte algo?")

        return _(
            "¿Qué plato te gustaría agregar a tu carrito? Puedes preguntarme por recomendaciones si no estás seguro.")