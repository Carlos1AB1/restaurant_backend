from elasticsearch_dsl import Search, Q
from elasticsearch import Elasticsearch
from django.conf import settings
import logging
from menu.models import Dish, Category

# Configurar logger
logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Servicio para realizar búsquedas en Elasticsearch.
    """

    @staticmethod
    def get_client():
        """
        Obtiene el cliente de Elasticsearch.

        Returns:
            Elasticsearch: Cliente de Elasticsearch
        """
        try:
            hosts = settings.ELASTICSEARCH_DSL.get('default', {}).get('hosts', 'localhost:9200')
            return Elasticsearch(hosts)
        except Exception as e:
            logger.error(f"Error al conectar con Elasticsearch: {str(e)}")
            return None

    @staticmethod
    def search_dishes(query, category=None, min_price=None, max_price=None):
        """
        Busca platos en Elasticsearch.

        Args:
            query: Texto de búsqueda
            category: ID de categoría (opcional)
            min_price: Precio mínimo (opcional)
            max_price: Precio máximo (opcional)

        Returns:
            list: Lista de IDs de platos que coinciden con la búsqueda
        """
        try:
            client = ElasticsearchService.get_client()

            if not client:
                # Fallback: búsqueda en base de datos
                return ElasticsearchService.fallback_search(query, category, min_price, max_price)

            # Iniciar búsqueda
            search = Search(using=client, index="dishes")

            # Construir consulta para texto
            must_queries = []

            if query:
                # Buscar en nombre y descripción
                text_query = Q(
                    "multi_match",
                    query=query,
                    fields=["name^3", "description", "category_name", "ingredients.name"],
                    fuzziness="AUTO"
                )
                must_queries.append(text_query)

            # Filtrar por categoría
            if category:
                must_queries.append(Q("term", category_id=str(category)))

            # Filtrar por rango de precio
            price_range = {}
            if min_price is not None:
                price_range["gte"] = float(min_price)
            if max_price is not None:
                price_range["lte"] = float(max_price)

            if price_range:
                must_queries.append(Q("range", price=price_range))

            # Solo platos activos
            must_queries.append(Q("term", is_active=True))

            # Combinar consultas
            if must_queries:
                search = search.query("bool", must=must_queries)

            # Ejecutar búsqueda
            response = search.execute()

            # Extraer IDs de platos
            dish_ids = [hit.meta.id for hit in response.hits]

            return dish_ids

        except Exception as e:
            logger.error(f"Error en búsqueda Elasticsearch: {str(e)}")
            # Fallback: búsqueda en base de datos
            return ElasticsearchService.fallback_search(query, category, min_price, max_price)

    @staticmethod
    def fallback_search(query, category=None, min_price=None, max_price=None):
        """
        Búsqueda de respaldo en base de datos cuando Elasticsearch no está disponible.

        Args:
            query: Texto de búsqueda
            category: ID de categoría (opcional)
            min_price: Precio mínimo (opcional)
            max_price: Precio máximo (opcional)

        Returns:
            list: Lista de IDs de platos que coinciden con la búsqueda
        """
        logger.warning("Utilizando búsqueda fallback en base de datos")

        # Iniciar con platos activos
        queryset = Dish.objects.filter(is_active=True)

        # Filtrar por texto de búsqueda
        if query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(ingredients__ingredient__name__icontains=query)
            ).distinct()

        # Filtrar por categoría
        if category:
            queryset = queryset.filter(category_id=category)

        # Filtrar por rango de precio
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        # Retornar IDs
        return [str(dish.id) for dish in queryset]

    @staticmethod
    def suggest_search(query):
        """
        Obtiene sugerencias de búsqueda basadas en texto parcial.

        Args:
            query: Texto parcial de búsqueda

        Returns:
            list: Lista de sugerencias
        """
        try:
            client = ElasticsearchService.get_client()

            if not client:
                # Fallback: sugerencias desde base de datos
                return ElasticsearchService.fallback_suggest(query)

            # Buscar sugerencias
            search = Search(using=client, index="dishes")

            # Combinar sugerencias de varios campos
            suggestions = []

            # Sugerencias de nombre de plato
            name_suggest = {
                "prefix": query,
                "completion": {
                    "field": "name_suggest",
                    "size": 5,
                    "fuzzy": {
                        "fuzziness": "AUTO"
                    }
                }
            }

            # Sugerencias de categoría
            category_suggest = {
                "prefix": query,
                "completion": {
                    "field": "category_suggest",
                    "size": 3
                }
            }

            # Sugerencias de ingredientes
            ingredient_suggest = {
                "prefix": query,
                "completion": {
                    "field": "ingredients_suggest",
                    "size": 3
                }
            }

            # Ejecutar sugerencias
            response = client.search(
                index="dishes",
                body={
                    "suggest": {
                        "dish_suggest": name_suggest,
                        "category_suggest": category_suggest,
                        "ingredient_suggest": ingredient_suggest
                    }
                }
            )

            # Procesar resultados
            if "suggest" in response:
                # Extraer sugerencias de nombre de plato
                if "dish_suggest" in response["suggest"]:
                    for option in response["suggest"]["dish_suggest"][0]["options"]:
                        suggestions.append(option["text"])

                # Extraer sugerencias de categoría
                if "category_suggest" in response["suggest"]:
                    for option in response["suggest"]["category_suggest"][0]["options"]:
                        suggestions.append(option["text"])

                # Extraer sugerencias de ingredientes
                if "ingredient_suggest" in response["suggest"]:
                    for option in response["suggest"]["ingredient_suggest"][0]["options"]:
                        suggestions.append(option["text"])

            # Eliminar duplicados y ordenar
            suggestions = list(set(suggestions))
            suggestions.sort()

            return suggestions

        except Exception as e:
            logger.error(f"Error en sugerencias Elasticsearch: {str(e)}")
            # Fallback: sugerencias desde base de datos
            return ElasticsearchService.fallback_suggest(query)

    @staticmethod
    def fallback_suggest(query):
        """
        Sugerencias de respaldo desde base de datos cuando Elasticsearch no está disponible.

        Args:
            query: Texto parcial de búsqueda

        Returns:
            list: Lista de sugerencias
        """
        logger.warning("Utilizando sugerencias fallback desde base de datos")

        suggestions = set()

        # Sugerencias desde nombres de platos
        dish_names = Dish.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:5]

        for name in dish_names:
            suggestions.add(name)

        # Sugerencias desde categorías
        category_names = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:3]

        for name in category_names:
            suggestions.add(name)

        # Sugerencias desde ingredientes
        ingredient_names = Dish.objects.filter(
            ingredients__ingredient__name__icontains=query,
            is_active=True
        ).values_list(
            'ingredients__ingredient__name',
            flat=True
        ).distinct()[:3]

        for name in ingredient_names:
            suggestions.add(name)

        # Convertir a lista y ordenar
        return sorted(list(suggestions))

    @staticmethod
    def index_dish(dish):
        """
        Indexa o actualiza un plato en Elasticsearch.

        Args:
            dish: Instancia del modelo Dish

        Returns:
            bool: True si la indexación fue exitosa
        """
        try:
            client = ElasticsearchService.get_client()

            if not client:
                logger.error("No se pudo conectar con Elasticsearch para indexar plato")
                return False

            # Preparar documento
            doc = {
                "id": str(dish.id),
                "name": dish.name,
                "description": dish.description,
                "price": float(dish.price),
                "category_id": str(dish.category.id),
                "category_name": dish.category.name,
                "is_featured": dish.is_featured,
                "is_active": dish.is_active,
                "preparation_time": dish.preparation_time,
                "calories": dish.calories,
                "name_suggest": dish.name,
                "category_suggest": dish.category.name,
                "ingredients": [],
                "ingredients_suggest": []
            }

            # Agregar ingredientes
            for dish_ingredient in dish.ingredients.all():
                ingredient = dish_ingredient.ingredient
                doc["ingredients"].append({
                    "id": str(ingredient.id),
                    "name": ingredient.name,
                    "is_allergen": ingredient.is_allergen
                })
                doc["ingredients_suggest"].append(ingredient.name)

            # Indexar documento
            client.index(
                index="dishes",
                id=str(dish.id),
                body=doc
            )

            # Refrescar índice para que los cambios sean visibles inmediatamente
            client.indices.refresh(index="dishes")

            logger.info(f"Plato indexado correctamente: {dish.name} ({dish.id})")
            return True

        except Exception as e:
            logger.error(f"Error al indexar plato {dish.id}: {str(e)}")
            return False

    @staticmethod
    def delete_dish(dish_id):
        """
        Elimina un plato del índice de Elasticsearch.

        Args:
            dish_id: ID del plato a eliminar

        Returns:
            bool: True si la eliminación fue exitosa
        """
        try:
            client = ElasticsearchService.get_client()

            if not client:
                logger.error("No se pudo conectar con Elasticsearch para eliminar plato")
                return False

            # Eliminar documento
            client.delete(
                index="dishes",
                id=str(dish_id)
            )

            # Refrescar índice
            client.indices.refresh(index="dishes")

            logger.info(f"Plato eliminado del índice: {dish_id}")
            return True

        except Exception as e:
            logger.error(f"Error al eliminar plato {dish_id} del índice: {str(e)}")
            return False

    @staticmethod
    def create_index():
        """
        Crea el índice de Elasticsearch con el mapping adecuado.

        Returns:
            bool: True si la creación fue exitosa
        """
        try:
            client = ElasticsearchService.get_client()

            if not client:
                logger.error("No se pudo conectar con Elasticsearch para crear índice")
                return False

            # Verificar si el índice ya existe
            if client.indices.exists(index="dishes"):
                logger.info("El índice 'dishes' ya existe")
                return True

            # Definir mapping
            mapping = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "spanish_analyzer": {
                                "type": "spanish"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "analyzer": "spanish_analyzer",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "description": {"type": "text", "analyzer": "spanish_analyzer"},
                        "price": {"type": "float"},
                        "category_id": {"type": "keyword"},
                        "category_name": {
                            "type": "text",
                            "analyzer": "spanish_analyzer",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "is_featured": {"type": "boolean"},
                        "is_active": {"type": "boolean"},
                        "preparation_time": {"type": "integer"},
                        "calories": {"type": "integer"},
                        "name_suggest": {
                            "type": "completion",
                            "analyzer": "spanish_analyzer"
                        },
                        "category_suggest": {
                            "type": "completion",
                            "analyzer": "spanish_analyzer"
                        },
                        "ingredients": {
                            "type": "nested",
                            "properties": {
                                "id": {"type": "keyword"},
                                "name": {"type": "text", "analyzer": "spanish_analyzer"},
                                "is_allergen": {"type": "boolean"}
                            }
                        },
                        "ingredients_suggest": {
                            "type": "completion",
                            "analyzer": "spanish_analyzer"
                        }
                    }
                }
            }

            # Crear índice
            client.indices.create(
                index="dishes",
                body=mapping
            )

            logger.info("Índice 'dishes' creado correctamente")
            return True

        except Exception as e:
            logger.error(f"Error al crear índice: {str(e)}")
            return False

    @staticmethod
    def reindex_all():
        """
        Reindexar todos los platos en Elasticsearch.

        Returns:
            int: Número de platos indexados
        """
        try:
            # Crear índice si no existe
            if not ElasticsearchService.create_index():
                return 0

            # Obtener todos los platos activos
            dishes = Dish.objects.filter(is_active=True).select_related('category').prefetch_related(
                'ingredients__ingredient')

            # Indexar cada plato
            indexed_count = 0
            for dish in dishes:
                if ElasticsearchService.index_dish(dish):
                    indexed_count += 1

            logger.info(f"Se indexaron {indexed_count} platos")
            return indexed_count

        except Exception as e:
            logger.error(f"Error al reindexar platos: {str(e)}")
            return 0