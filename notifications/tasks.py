from celery import shared_task
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import logging

from users.models import User
from orders.models import Order
from .services import send_order_status_update_email

# Configurar logger
logger = logging.getLogger(__name__)


@shared_task
def send_order_reminders():
    """
    Tarea para enviar recordatorios de pedidos pendientes.
    """
    try:
        # Buscar pedidos confirmados pero no entregados
        pending_orders = Order.objects.filter(
            status__in=['CONFIRMED', 'PREPARING', 'READY', 'OUT_FOR_DELIVERY'],
            created_at__lte=timezone.now() - timedelta(hours=1)  # Pedidos con más de 1 hora
        )

        for order in pending_orders:
            try:
                # Enviar email de recordatorio
                send_order_status_update_email(order)
                logger.info(f"Recordatorio enviado para pedido #{order.order_number}")
            except Exception as e:
                logger.error(f"Error al enviar recordatorio para pedido #{order.order_number}: {str(e)}")

        return f"Procesados {pending_orders.count()} recordatorios de pedidos"

    except Exception as e:
        logger.error(f"Error en tarea send_order_reminders: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def clean_unverified_users():
    """
    Tarea para limpiar usuarios no verificados después de cierto tiempo.
    """
    try:
        # Buscar usuarios no verificados con más de 3 días
        expiration_date = timezone.now() - timedelta(days=3)
        unverified_users = User.objects.filter(
            email_verified=False,
            date_joined__lte=expiration_date
        )

        count = unverified_users.count()

        # Eliminar usuarios
        unverified_users.delete()

        logger.info(f"Eliminados {count} usuarios no verificados")
        return f"Eliminados {count} usuarios no verificados"

    except Exception as e:
        logger.error(f"Error en tarea clean_unverified_users: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_promotional_emails():
    """
    Tarea para enviar correos promocionales a usuarios activos.
    """
    try:
        # Esta tarea es un ejemplo. La implementación real dependerá de la lógica de negocio.
        # Aquí se colocaría el código para seleccionar promociones y enviar emails.
        logger.info("Tarea send_promotional_emails ejecutada")
        return "Tarea de emails promocionales completada"

    except Exception as e:
        logger.error(f"Error en tarea send_promotional_emails: {str(e)}")
        return f"Error: {str(e)}"