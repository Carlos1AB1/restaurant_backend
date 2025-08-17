from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'
    verbose_name = "Gestión de Reseñas y Calificaciones"

    # No necesitas llamar a signals aquí si usaste decoradores @receiver en models.py
    # def ready(self):
    #     import apps.reviews.signals