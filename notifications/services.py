from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
import logging
import socket

# Configurar logger
logger = logging.getLogger(__name__)


def send_html_email(subject, template_path, context, recipient_list):
    """
    Envía un correo electrónico HTML con manejo de errores mejorado.

    Args:
        subject (str): Asunto del correo
        template_path (str): Ruta de la plantilla HTML
        context (dict): Contexto para renderizar la plantilla
        recipient_list (list): Lista de destinatarios

    Returns:
        bool: True si el correo se envió correctamente, False en caso de error
    """
    try:
        # Renderizar contenido HTML
        html_content = render_to_string(template_path, context)

        # Crear mensaje de correo
        email = EmailMultiAlternatives(
            subject=subject,
            body='',  # Texto plano alternativo
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )

        # Adjuntar contenido HTML
        email.attach_alternative(html_content, "text/html")

        # Configurar timeout para la conexión
        socket.setdefaulttimeout(10)  # 10 segundos de timeout

        # Enviar correo
        result = email.send()

        if result:
            logger.info(f"Correo enviado exitosamente a {recipient_list}")
            return True
        else:
            logger.warning(f"Fallo al enviar correo a {recipient_list}")
            return False

    except socket.timeout:
        logger.error(f"Timeout al enviar correo a {recipient_list}")
        return False
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        # Opcional: Puedes agregar más detalles de registro aquí
        return False


def send_verification_email(user):
    """
    Envía un correo electrónico de verificación al usuario.

    Args:
        user: Instancia del modelo User

    Returns:
        bool: True si el correo se envió correctamente
    """
    try:
        # Usar getattr para proporcionar un valor predeterminado
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

        subject = _('Verifica tu cuenta de Restaurant App')

        # Construir enlace de verificación
        verification_url = f"{frontend_url}/verify-email?token={user.verification_token}"

        # Enviar correo usando la nueva función
        return send_html_email(
            subject=subject,
            template_path='emails/verification_email.html',
            context={
                'user': user,
                'verification_url': verification_url,
                'expiration_hours': 24,
            },
            recipient_list=[user.email]
        )

    except Exception as e:
        logger.error(f"Error en send_verification_email para {user.email}: {str(e)}")
        return False


def send_password_reset_email(user):
    """
    Envía un correo electrónico con instrucciones para restablecer contraseña.

    Args:
        user: Instancia del modelo User

    Returns:
        bool: True si el correo se envió correctamente
    """
    try:
        subject = _('Restablece tu contraseña - Restaurant App')

        # Construir enlace de restablecimiento
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={user.password_reset_token}"

        # Enviar correo usando la nueva función
        return send_html_email(
            subject=subject,
            template_path='emails/password_reset_email.html',
            context={
                'user': user,
                'reset_url': reset_url,
                'expiration_hours': 24,
            },
            recipient_list=[user.email]
        )

    except Exception as e:
        logger.error(f"Error en send_password_reset_email para {user.email}: {str(e)}")
        return False


def send_order_confirmation_email(order):
    """
    Envía un correo electrónico de confirmación de pedido.

    Args:
        order: Instancia del modelo Order

    Returns:
        bool: True si el correo se envió correctamente
    """
    try:
        subject = _('Confirmación de Pedido #{} - Restaurant App').format(order.order_number)

        # Construir enlace de seguimiento de pedido
        order_url = f"{settings.FRONTEND_URL}/orders/{order.id}"

        # Enviar correo usando la nueva función
        return send_html_email(
            subject=subject,
            template_path='emails/order_confirmation_email.html',
            context={
                'user': order.user,
                'order': order,
                'order_url': order_url,
                'order_items': order.items.all(),
            },
            recipient_list=[order.user.email]
        )

    except Exception as e:
        logger.error(f"Error en send_order_confirmation_email para {order.user.email}: {str(e)}")
        return False


def send_order_status_update_email(order):
    """
    Envía un correo electrónico de actualización de estado de pedido.

    Args:
        order: Instancia del modelo Order

    Returns:
        bool: True si el correo se envió correctamente
    """
    try:
        subject = _('Actualización de Pedido #{} - Restaurant App').format(order.order_number)

        # Construir enlace de seguimiento de pedido
        order_url = f"{settings.FRONTEND_URL}/orders/{order.id}"

        # Enviar correo usando la nueva función
        return send_html_email(
            subject=subject,
            template_path='emails/order_status_update_email.html',
            context={
                'user': order.user,
                'order': order,
                'order_url': order_url,
            },
            recipient_list=[order.user.email]
        )

    except Exception as e:
        logger.error(f"Error en send_order_status_update_email para {order.user.email}: {str(e)}")
        return False