from rest_framework import generics, permissions
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
from .serializers import ContactMessageSerializer

class ContactMessageCreateView(generics.CreateAPIView):
    """
    Permite a cualquier usuario enviar un mensaje de contacto.
    Envía una notificación por email al correo del restaurante.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny] # Cualquiera puede enviar mensaje

    def perform_create(self, serializer):
        contact_message = serializer.save()
        # Enviar notificación por email al restaurante
        self.send_notification_email(contact_message)

    def send_notification_email(self, contact_message):
        """Envía un email al correo configurado en settings."""
        subject = f"Nuevo Mensaje de Contacto: {contact_message.subject}"
        message_body = f"""
Has recibido un nuevo mensaje de contacto a través del sitio web:

Nombre: {contact_message.name}
Email: {contact_message.email}
Asunto: {contact_message.subject}

Mensaje:
--------------------------------
{contact_message.message}
--------------------------------

Fecha: {contact_message.created_at.strftime('%d/%m/%Y %H:%M')}
"""
        recipient_email = settings.RESTAURANT_CONTACT_EMAIL

        if not recipient_email:
            print("ADVERTENCIA: No se ha configurado RESTAURANT_CONTACT_EMAIL en .env. No se enviará notificación.")
            return

        try:
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL, # Remitente (puede ser el mismo que el de notificaciones)
                [recipient_email], # Destinatario (el email del restaurante)
                fail_silently=False,
            )
            print(f"Notificación de contacto enviada a {recipient_email}")
        except Exception as e:
            print(f"Error al enviar notificación de contacto a {recipient_email}: {e}")

# Si necesitas listar/ver mensajes (solo para admins), puedes añadir un ViewSet:
# from rest_framework import viewsets
# class ContactMessageViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = ContactMessage.objects.all()
#     serializer_class = ContactMessageSerializer
#     permission_classes = [permissions.IsAdminUser]