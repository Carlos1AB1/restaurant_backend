from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from .models import Dish
from search.services import ElasticsearchService

# Configurar logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Dish)
def index_dish(sender, instance, created, **kwargs):
    """
    Signal para indexar plato en Elasticsearch cuando se crea o actualiza.
    """
    try:
        if instance.is_active:
            # Indexar plato
            ElasticsearchService.index_dish(instance)
            logger.info(f"Plato indexado por signal: {instance.name} ({instance.id})")
        else:
            # Si el plato no está activo, eliminarlo del índice
            ElasticsearchService.delete_dish(instance.id)
            logger.info(f"Plato eliminado del índice por signal (inactivo): {instance.name} ({instance.id})")
    except Exception as e:
        logger.error(f"Error al indexar plato por signal: {str(e)}")


@receiver(post_delete, sender=Dish)
def delete_dish_from_index(sender, instance, **kwargs):
    """
    Signal para eliminar plato de Elasticsearch cuando se elimina.
    """
    try:
        # Eliminar plato del índice
        ElasticsearchService.delete_dish(instance.id)
        logger.info(f"Plato eliminado del índice por signal (delete): {instance.name} ({instance.id})")
    except Exception as e:
        logger.error(f"Error al eliminar plato del índice por signal: {str(e)}")