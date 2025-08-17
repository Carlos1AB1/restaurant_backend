from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string # Para templates de email HTML
from django.utils.html import strip_tags

from .models import Order
from apps.invoices.utils import generate_invoice_pdf # Importar función de facturas

# Variable global para almacenar el estado anterior
_old_order_status = {}

@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    """
    Captura el estado anterior del pedido antes de guardarlo
    """
    if instance.pk:  # Solo si el objeto ya existe (no es nuevo)
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            _old_order_status[instance.pk] = old_instance.status
        except Order.DoesNotExist:
            _old_order_status[instance.pk] = None

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Se ejecuta después de guardar un pedido.
    Envía email de confirmación al crearse o email de actualización de estado.
    Genera y adjunta factura (o la envía por separado) cuando el estado es apropiado.
    """
    order = instance
    user = order.user

    if not user: # No hacer nada si no hay usuario asociado (poco probable pero posible)
        return

    # --- Notificación por Email ---
    subject = ""
    message_txt = ""
    message_html = "" # Para emails HTML

    if created:
        # Email de Confirmación de Pedido Nuevo
        subject = f"Confirmación de tu pedido #{order.order_number} en {settings.RESTAURANT_NAME}"
        context = {'order': order, 'user': user, 'restaurant_name': settings.RESTAURANT_NAME}
        message_html = render_to_string('emails/order_confirmation.html', context)
        message_txt = strip_tags(message_html) # Versión texto plano

        # --- Generación/Envío de Factura (si aplica al confirmar) ---
        # Decide cuándo generar/enviar la factura. ¿Al confirmar? ¿Al entregar?
        # Aquí la generaremos y enviaremos al confirmar.
        try:
            pdf_content = generate_invoice_pdf(order)
            # Enviar email con factura adjunta
            send_order_email_with_attachment(
                subject, message_txt, user.email,
                attachment_content=pdf_content,
                attachment_filename=f"factura_{order.order_number}.pdf",
                html_message=message_html
            )
            print(f"Email de confirmación y factura enviados para pedido {order.order_number}")

        except Exception as e:
            print(f"Error generando o enviando factura para pedido {order.order_number}: {e}")
            # Enviar solo confirmación si falla la factura
            send_order_email(subject, message_txt, user.email, html_message=message_html)
            print(f"Email de confirmación (sin factura) enviado para pedido {order.order_number}")

    else:
        # Email de Actualización de Estado (Opcional)
        # Verificar si el estado cambió comparando con el estado anterior
        old_status = _old_order_status.get(order.pk)
        
        if old_status and old_status != order.status:
            # El estado cambió, enviar notificaciones apropiadas
            if order.status == 'OUT_FOR_DELIVERY':
                subject = f"¡Tu pedido #{order.order_number} está en camino! - {settings.RESTAURANT_NAME}"
                context = {'order': order, 'user': user, 'restaurant_name': settings.RESTAURANT_NAME}
                message_html = render_to_string('emails/order_out_for_delivery.html', context)
                message_txt = strip_tags(message_html)
                send_order_email(subject, message_txt, user.email, html_message=message_html)
                print(f"Email de 'En Reparto' enviado para pedido {order.order_number} (cambio de {old_status} a {order.status})")

            elif order.status == 'DELIVERED':
                subject = f"¡Tu pedido #{order.order_number} ha sido entregado! - {settings.RESTAURANT_NAME}"
                context = {'order': order, 'user': user, 'restaurant_name': settings.RESTAURANT_NAME}
                # Podrías incluir enlace para dejar reseña aquí
                message_html = render_to_string('emails/order_delivered.html', context)
                message_txt = strip_tags(message_html)
                send_order_email(subject, message_txt, user.email, html_message=message_html)
                print(f"Email de 'Entregado' enviado para pedido {order.order_number} (cambio de {old_status} a {order.status})")

            # Podrías añadir notificaciones para otros estados (CANCELLED, etc.)
            
        # Limpiar el estado anterior después de procesar
        if order.pk in _old_order_status:
            del _old_order_status[order.pk]


# --- Funciones Helper para enviar emails ---

def send_order_email(subject, message_txt, recipient_email, html_message=None):
    """Función helper para enviar emails simples."""
    try:
        send_mail(
            subject,
            message_txt,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
            html_message=html_message,
        )
    except Exception as e:
        print(f"Error al enviar email a {recipient_email}: {e}")

def send_order_email_with_attachment(subject, message_txt, recipient_email, attachment_content, attachment_filename, html_message=None):
    """Función helper para enviar emails con adjuntos."""
    from django.core.mail import EmailMessage
    try:
        email = EmailMessage(
            subject,
            message_txt, # Body (texto plano)
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email]
        )
        if html_message:
            email.content_subtype = "html" # Main content is now HTML
            email.body = html_message
            # Podrías añadir versión alternativa de texto plano si quieres:
            # email.attach_alternative(message_txt, "text/plain")

        # Adjuntar el PDF
        email.attach(attachment_filename, attachment_content, 'application/pdf')
        email.send(fail_silently=False)

    except Exception as e:
         print(f"Error al enviar email con adjunto a {recipient_email}: {e}")