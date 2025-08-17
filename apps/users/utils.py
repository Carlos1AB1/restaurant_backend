import os
import traceback # Importar para mejor debugging si es necesario

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verification_email(user, token_obj):
    """Envía el email de verificación al usuario usando plantilla HTML."""
    subject = f"Verifica tu cuenta en {os.getenv('RESTAURANT_NAME', 'Nuestro Restaurante')}"
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    verification_url = f"{frontend_url}/verify-email/{token_obj.token}/"

    context = {
        'user': user,
        'verification_url': verification_url,
        'restaurant_name': os.getenv('RESTAURANT_NAME', 'Nuestro Restaurante')
    }

    try:
        html_message = render_to_string('emails/verify_email.html', context)
        plain_message = strip_tags(html_message)

        # ---- AÑADIR ESTAS LÍNEAS PARA DEBUG ----
        print("--- DEBUG EMAIL CONTENT ---")
        print(f"Subject Type: {type(subject)}, Content: {subject!r}") # !r muestra repr()
        print(f"Plain Message Type: {type(plain_message)}, Snippet: {plain_message[:100]!r}...") # Primeros 100 chars
        # print(f"HTML Message Type: {type(html_message)}") # El HTML suele ser largo
        print("---------------------------")
        # ---- FIN DEBUG ----

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        print(f"Email de verificación (HTML) enviado exitosamente a {user.email}")
        return True

    except Exception as e:
        print(f"ERROR al enviar email de verificación a {user.email}: {e}")
        # import traceback # Descomenta para ver error completo
        # print(traceback.format_exc())
        return False


def send_password_reset_email(user, token_obj):
    """
    Envía el email de reseteo de contraseña al usuario usando la plantilla HTML.
    """
    subject = f"Restablecimiento de contraseña para {os.getenv('RESTAURANT_NAME', 'Nuestro Restaurante')}"
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    # Construir la URL completa de reseteo que el frontend manejará
    reset_url = f"{frontend_url}/reset-password/{token_obj.token}/"

    # Preparar el contexto para la plantilla HTML
    context = {
        'user': user,
        'reset_url': reset_url, # URL para el botón/enlace de reseteo
        'restaurant_name': os.getenv('RESTAURANT_NAME', 'Nuestro Restaurante')
    }

    try:
        # Renderizar la plantilla HTML
        html_message = render_to_string('emails/reset_password.html', context)
        # Crear versión de texto plano
        plain_message = strip_tags(html_message)

        # Enviar el correo
        send_mail(
            subject=subject,
            message=plain_message, # Texto plano
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False, # Lanza errores
            html_message=html_message # Versión HTML
        )
        # Log de éxito
        print(f"Email de reseteo de contraseña (HTML) enviado exitosamente a {user.email}")
        return True # Éxito

    except Exception as e:
        # Loggear el error
        print(f"ERROR al enviar email de reseteo de contraseña a {user.email}: {e}")
        # Opcional: Imprimir traceback completo
        # print("--- Traceback Completo del Error de Email ---")
        # print(traceback.format_exc())
        # print("--------------------------------------------")
        return False # Error