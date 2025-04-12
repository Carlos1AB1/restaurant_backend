# restaurant_backend/apps/invoices/urls.py

from django.urls import path
# Asegúrate de que la importación de tu vista sea correcta
from .views import DownloadInvoiceView

# ESTA LISTA ES LA QUE DJANGO BUSCA:
urlpatterns = [
    # Define la ruta para descargar la factura.
    # Usa <uuid:order_pk> porque el ID del modelo Order es un UUIDField.
    path('download/<uuid:order_pk>/', DownloadInvoiceView.as_view(), name='download-invoice'),

    # Puedes añadir más rutas relacionadas con facturas aquí si las necesitas en el futuro.
]

# Asegúrate de que NO haya otra definición de urlpatterns = [] vacía más abajo o
# algún error de sintaxis antes de esta definición.