from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class Conversation(models.Model):
    """
    Modelo para conversaciones de chatbot.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=_('usuario'),
        null=True,
        blank=True
    )
    # Para usuarios no autenticados, usar session_id
    session_id = models.CharField(
        _('ID de sesión'),
        max_length=100,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)
    is_active = models.BooleanField(_('activo'), default=True)

    class Meta:
        verbose_name = _('conversación')
        verbose_name_plural = _('conversaciones')
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"Conversación de {self.user.username} ({self.created_at})"
        return f"Conversación de invitado ({self.session_id}) ({self.created_at})"


class Message(models.Model):
    """
    Modelo para mensajes en una conversación de chatbot.
    """
    SENDER_CHOICES = (
        ('USER', _('Usuario')),
        ('BOT', _('Chatbot')),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversación')
    )
    sender = models.CharField(
        _('remitente'),
        max_length=10,
        choices=SENDER_CHOICES
    )
    content = models.TextField(_('contenido'))
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)

    class Meta:
        verbose_name = _('mensaje')
        verbose_name_plural = _('mensajes')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:50]}..."


class Intent(models.Model):
    """
    Modelo para intenciones reconocidas por el chatbot.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(_('nombre'), max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    examples = models.TextField(
        _('ejemplos'),
        help_text=_('Ejemplos de frases para entrenar, uno por línea')
    )
    response_template = models.TextField(
        _('plantilla de respuesta'),
        help_text=_('Plantilla para generar respuestas')
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('intención')
        verbose_name_plural = _('intenciones')
        ordering = ['name']

    def __str__(self):
        return self.name


class RecommendationLog(models.Model):
    """
    Modelo para registrar recomendaciones del chatbot.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='recommendations',
        verbose_name=_('usuario'),
        null=True,
        blank=True
    )
    session_id = models.CharField(_('ID de sesión'), max_length=100, null=True, blank=True)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('mensaje')
    )
    dish = models.ForeignKey(
        'menu.Dish',
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('plato')
    )
    context = models.TextField(_('contexto'), blank=True)
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)

    class Meta:
        verbose_name = _('registro de recomendación')
        verbose_name_plural = _('registros de recomendaciones')
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else f"Invitado ({self.session_id})"
        return f"Recomendación de {self.dish.name} para {user_str}"