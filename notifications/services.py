from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
import logging

# Configurar logger
logger = logging.getLogger(__name__)


def send_verification_email(user):
    """
    Envía un correo electrónico de verificación al usuario.

    Args:
        user: Instancia del modelo User
    """
    try:
        subject = _('Verifica tu cuenta de Restaurant App')

        # Construir enlace de verificación
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.verification_token}"

        # Contenido del correo
        message = render_to_string('emails/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
            'expiration_hours': 24,
        })

        # Enviar correo
        send_mail(
            subject,
            '',  # Mensaje en texto plano (vacío porque usamos HTML)
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )

        logger.info(f"Email de verificación enviado a {user.email}")

    except Exception as e:
        logger.error(f"Error al enviar email de verificación a {user.email}: {str(e)}")


def send_password_reset_email(user):
    """
    Envía un correo electrónico con instrucciones para restablecer contraseña.

    Args:
        user: Instancia del modelo User
    """
    try:
        subject = _('Restablece tu contraseña - Restaurant App')

        # Construir enlace de restablecimiento
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={user.password_reset_token}"

        # Contenido del correo
        message = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'expiration_hours': 24,
        })

        # Enviar correo
        send_mail(
            subject,
            '',  # Mensaje en texto plano (vacío porque usamos HTML)
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )

        logger.info(f"Email de restablecimiento de contraseña enviado a {user.email}")

    except Exception as e:
        logger.error(f"Error al enviar email de restablecimiento a {user.email}: {str(e)}")


def send_order_confirmation_email(order):
    """
    Envía un correo electrónico de confirmación de pedido.

    Args:
        order: Instancia del modelo Order
    """
    try:
        user = order.user
        subject = _('Confirmación de Pedido #{} - Restaurant App').format(order.order_number)

        # Construir enlace de seguimiento de pedido
        order_url = f"{settings.FRONTEND_URL}/orders/{order.id}"

        # Contenido del correo
        message = render_to_string('emails/order_confirmation_email.html', {
            'user': user,
            'order': order,
            'order_url': order_url,
            'order_items': order.items.all(),
        })

        # Enviar correo
        send_mail(
            subject,
            '',  # Mensaje en texto plano (vacío porque usamos HTML)
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )

        logger.info(f"Email de confirmación de pedido enviado a {user.email} para el pedido {order.id}")

    except Exception as e:
        logger.error(f"Error al enviar email de confirmación de pedido a {user.email}: {str(e)}")


def send_order_status_update_email(order):
    """
    Envía un correo electrónico de actualización de estado de pedido.

    Args:
        order: Instancia del modelo Order
    """
    try:
        user = order.user
        subject = _('Actualización de Pedido #{} - Restaurant App').format(order.order_number)

        # Contenido del correo
        message = render_to_string('emails/order_status_update_email.html', {
            'user': user,
            'order': order,
            'order_url': f"{settings.FRONTEND_URL}/orders/{order.id}",
        })

        # Enviar correo
        send_mail(
            subject,
            '',  # Mensaje en texto plano (vacío porque usamos HTML)
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )

        logger.info(f"Email de actualización de estado de pedido enviado a {user.email} para el pedido {order.id}")

    except Exception as e:
        logger.error(f"Error al enviar email de actualización de estado de pedido a {user.email}: {str(e)}")