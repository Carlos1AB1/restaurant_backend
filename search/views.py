from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
import logging

from menu.models import Dish
from menu.serializers import DishListSerializer
from .services import ElasticsearchService

# Configurar logger
logger = logging.getLogger(__name__)


class SearchDishesView(APIView):
    """
    Vista para buscar platos.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Extraer parámetros de búsqueda
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)

        try:
            # Realizar búsqueda
            dish_ids = ElasticsearchService.search_dishes(
                query=query,
                category=category,
                min_price=min_price,
                max_price=max_price
            )

            # Obtener platos desde la base de datos
            # Nota: Preservar el orden de la búsqueda
            dishes = []
            if dish_ids:
                # Crear diccionario para mantener el orden
                dishes_dict = {str(dish.id): dish for dish in Dish.objects.filter(id__in=dish_ids)}
                dishes = [dishes_dict[dish_id] for dish_id in dish_ids if dish_id in dishes_dict]

            # Serializar resultados
            serializer = DishListSerializer(dishes, many=True)

            return Response({
                'count': len(dishes),
                'results': serializer.data
            })

        except Exception as e:
            logger.error(f"Error en búsqueda: {str(e)}")
            return Response(
                {"detail": _("Error al procesar la búsqueda.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchSuggestionsView(APIView):
    """
    Vista para obtener sugerencias de búsqueda.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Extraer texto parcial
        query = request.query_params.get('q', '')

        if not query or len(query) < 2:
            return Response([])

        try:
            # Obtener sugerencias
            suggestions = ElasticsearchService.suggest_search(query)

            return Response(suggestions)

        except Exception as e:
            logger.error(f"Error en sugerencias: {str(e)}")
            return Response(
                {"detail": _("Error al procesar las sugerencias.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReindexView(APIView):
    """
    Vista para reindexar platos en Elasticsearch.
    Solo accesible por administradores.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        try:
            # Reindexar todos los platos
            indexed_count = ElasticsearchService.reindex_all()

            return Response({
                "detail": _("Reindexación completada."),
                "indexed_count": indexed_count
            })

        except Exception as e:
            logger.error(f"Error en reindexación: {str(e)}")
            return Response(
                {"detail": _("Error al reindexar platos: {}").format(str(e))},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )