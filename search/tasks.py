from celery import shared_task
import logging

from .services import ElasticsearchService

# Configurar logger
logger = logging.getLogger(__name__)


@shared_task
def reindex_all_dishes():
    """
    Tarea para reindexar todos los platos en Elasticsearch.
    """
    try:
        # Reindexar todos los platos
        indexed_count = ElasticsearchService.reindex_all()

        logger.info(f"Reindexados {indexed_count} platos")
        return f"Reindexados {indexed_count} platos"

    except Exception as e:
        logger.error(f"Error en tarea reindex_all_dishes: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def check_elasticsearch_connection():
    """
    Tarea para verificar la conexión con Elasticsearch.
    """
    try:
        # Obtener cliente
        client = ElasticsearchService.get_client()

        if client is None:
            logger.error("No se pudo obtener cliente de Elasticsearch")
            return "Error: No se pudo obtener cliente de Elasticsearch"

        # Verificar conexión
        if client.ping():
            logger.info("Conexión con Elasticsearch exitosa")
            return "Conexión con Elasticsearch exitosa"
        else:
            logger.error("Error de conexión con Elasticsearch: ping falló")
            return "Error: ping a Elasticsearch falló"

    except Exception as e:
        logger.error(f"Error al verificar conexión con Elasticsearch: {str(e)}")
        return f"Error: {str(e)}"