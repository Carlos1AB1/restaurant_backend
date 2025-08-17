from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status

from apps.orders.models import Order
from .utils import generate_invoice_pdf

class DownloadInvoiceView(APIView):
    """
    Permite a un usuario autenticado descargar la factura de SU pedido,
    o a un administrador descargar la factura de CUALQUIER pedido.
    """
    permission_classes = [IsAuthenticated] # Requerir autenticación base

    def get(self, request, order_pk, *args, **kwargs):
        try:
            order = get_object_or_404(Order, pk=order_pk)

            # Verificar permisos: ¿Es el dueño del pedido o es admin?
            if not (order.user == request.user or request.user.is_staff):
                 return HttpResponse("No tienes permiso para ver esta factura.", status=status.HTTP_403_FORBIDDEN)

            # Generar el PDF
            try:
                pdf_content = generate_invoice_pdf(order)
            except Exception as e:
                 # Loggear el error e informar al usuario
                 print(f"Error generando PDF para factura {order.order_number} (descarga): {e}")
                 return HttpResponse("Error al generar la factura en PDF.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Preparar la respuesta HTTP con el PDF
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="factura_{order.order_number}.pdf"'
            # 'inline' intenta mostrarlo en el navegador, 'attachment' fuerza la descarga

            return response

        except Http404:
            return HttpResponse("Pedido no encontrado.", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error inesperado en DownloadInvoiceView para order_pk {order_pk}: {e}")
            return HttpResponse("Ocurrió un error inesperado.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)