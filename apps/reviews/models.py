from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.menu.models import Product

class Review(models.Model):
    """Reseña de un producto hecha por un usuario."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Producto")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', verbose_name="Usuario")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Calificación (1-5)"
    )
    comment = models.TextField(blank=True, verbose_name="Comentario")
    is_approved = models.BooleanField(default=False, verbose_name="Aprobada") # Moderación por admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user') # Un usuario solo puede reseñar un producto una vez
        ordering = ['-created_at']
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"

    def __str__(self):
        return f"Reseña de {self.user.email} para {self.product.name} ({self.rating} estrellas)"

# --- Señales para actualizar calificación promedio del producto ---

@receiver([post_save, post_delete], sender=Review)
def update_product_average_rating(sender, instance, **kwargs):
    """
    Actualiza la calificación promedio del producto cuando una reseña
    se guarda (y está aprobada) o se elimina.
    """
    # Solo recalcular si la reseña está aprobada o si se está eliminando
    # (porque una reseña eliminada ya no cuenta, aprobada o no)
    # El 'created' flag no es fiable con post_delete
    # Usamos 'update_fields' para saber si is_approved cambió en un save
    update_fields = kwargs.get('update_fields')
    approved_changed = update_fields and 'is_approved' in update_fields
    is_deletion = kwargs.get('signal') == post_delete

    # Recalcular si:
    # 1. Se está borrando la reseña.
    # 2. Se está guardando Y (está aprobada O el campo 'is_approved' acaba de cambiar).
    #    Esto cubre casos: nueva reseña aprobada, reseña existente aprobada, reseña desaprobada.
    should_recalculate = is_deletion or (instance.is_approved or approved_changed)

    if should_recalculate:
        # instance.product.update_average_rating() # Llama al método en el modelo Product
        # Necesitamos esperar a que la transacción termine, especialmente en deletes
        from django.db import transaction
        transaction.on_commit(lambda: instance.product.update_average_rating())