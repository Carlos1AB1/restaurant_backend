from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging
import json

from orders.models import Order, OrderStatusHistory
from .serializers import (
    PaymentIntentCreateSerializer,
    PaymentConfirmSerializer,
    PaymentRefundSerializer
)
from .services import StripeService
from notifications.services import send_order_confirmation_email

# Configurar logger
logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Vista para crear un intento de pago con Stripe.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentIntentCreateSerializer(data=request.data)

        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']

            # Verificar que el pedido existe y pertenece al usuario
            try:
                order = Order.objects.get(id=order_id, user=request.user)

                # Verificar que el pedido está pendiente de pago
                if order.payment_status == 'completed':
                    return Response(
                        {"detail": _("Este pedido ya ha sido pagado.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Crear intento de pago
                payment_data = StripeService.create_payment_intent(order)

                return Response(payment_data, status=status.HTTP_200_OK)

            except Order.DoesNotExist:
                return Response(
                    {"detail": _("Pedido no encontrado.")},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmPaymentView(APIView):
    """
    Vista para confirmar un pago con Stripe.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PaymentConfirmSerializer(data=request.data)

        if serializer.is_valid():
            payment_intent_id = serializer.validated_data['payment_intent_id']
            order_id = serializer.validated_data['order_id']

            # Verificar que el pedido existe y pertenece al usuario
            try:
                order = Order.objects.get(id=order_id, user=request.user)

                # Verificar que el payment_intent_id coincide con el del pedido
                if order.payment_id != payment_intent_id:
                    return Response(
                        {"detail": _("El ID de pago no coincide con el del pedido.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Confirmar pago
                payment_confirmed = StripeService.confirm_payment(payment_intent_id)

                if payment_confirmed:
                    # Actualizar estado del pedido
                    order.payment_status = 'completed'
                    order.status = 'CONFIRMED'
                    order.save()

                    # Registrar cambio en historial
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='CONFIRMED',
                        notes=_("Pago confirmado")
                    )

                    # Enviar email de confirmación
                    send_order_confirmation_email(order)

                    return Response(
                        {"detail": _("Pago confirmado correctamente.")},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"detail": _("El pago no ha sido completado.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except Order.DoesNotExist:
                return Response(
                    {"detail": _("Pedido no encontrado.")},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefundPaymentView(APIView):
    """
    Vista para reembolsar un pago con Stripe.
    Solo accesible por administradores.
    """
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request):
        serializer = PaymentRefundSerializer(data=request.data)

        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            amount = serializer.validated_data.get('amount', None)

            # Verificar que el pedido existe
            try:
                order = get_object_or_404(Order, id=order_id)

                # Verificar que el pedido ha sido pagado
                if order.payment_status != 'completed':
                    return Response(
                        {"detail": _("Solo se pueden reembolsar pedidos pagados.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Procesar reembolso
                refund_data = StripeService.refund_payment(order.payment_id, amount)

                # Actualizar estado del pedido
                if amount is None or (amount and amount >= order.total * 100):
                    order.payment_status = 'refunded'
                    order.status = 'CANCELLED'
                else:
                    order.payment_status = 'partially_refunded'

                order.save()

                # Registrar cambio en historial
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order.status,
                    notes=_("Reembolso procesado: {}").format(refund_data['refund_id'])
                )

                return Response(
                    {
                        "detail": _("Reembolso procesado correctamente."),
                        "refund_data": refund_data
                    },
                    status=status.HTTP_200_OK
                )

            except Order.DoesNotExist:
                return Response(
                    {"detail": _("Pedido no encontrado.")},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    """
    Vista para manejar webhooks de Stripe.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # No authentication for webhooks

    @transaction.atomic
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            logger.error("No se encontró la firma de Stripe en la solicitud")
            return HttpResponse(status=400)

        try:
            event = StripeService.process_webhook(payload, sig_header)

            # Manejar eventos específicos
            if event['type'] == 'payment_intent.succeeded':
                self._handle_payment_succeeded(event['data']['object'])

            elif event['type'] == 'payment_intent.payment_failed':
                self._handle_payment_failed(event['data']['object'])

            elif event['type'] == 'charge.refunded':
                self._handle_charge_refunded(event['data']['object'])

            # Devolver respuesta exitosa para todos los eventos
            return HttpResponse(status=200)

        except ValueError as e:
            logger.error(f"Error en webhook: {str(e)}")
            return HttpResponse(status=400)

    def _handle_payment_succeeded(self, payment_intent):
        """Maneja evento de pago exitoso."""
        logger.info(f"Pago exitoso: {payment_intent.id}")

        # Buscar pedido asociado
        try:
            order = Order.objects.get(payment_id=payment_intent.id)

            # Actualizar estado del pedido si aún no se ha actualizado
            if order.payment_status != 'completed':
                order.payment_status = 'completed'
                order.status = 'CONFIRMED'
                order.save()

                # Registrar cambio en historial
                OrderStatusHistory.objects.create(
                    order=order,
                    status='CONFIRMED',
                    notes=_("Pago confirmado por webhook")
                )

                # Enviar email de confirmación
                send_order_confirmation_email(order)

        except Order.DoesNotExist:
            logger.warning(f"No se encontró pedido para el pago {payment_intent.id}")

    def _handle_payment_failed(self, payment_intent):
        """Maneja evento de pago fallido."""
        logger.info(f"Pago fallido: {payment_intent.id}")

        # Buscar pedido asociado
        try:
            order = Order.objects.get(payment_id=payment_intent.id)

            # Actualizar estado del pedido
            order.payment_status = 'failed'
            order.save()

            # Registrar cambio en historial
            OrderStatusHistory.objects.create(
                order=order,
                status='PENDING',
                notes=_("Pago fallido: {}").format(
                    payment_intent.get('last_payment_error', {}).get('message', 'Error desconocido')
                )
            )

        except Order.DoesNotExist:
            logger.warning(f"No se encontró pedido para el pago {payment_intent.id}")

    def _handle_charge_refunded(self, charge):
        """Maneja evento de cargo reembolsado."""
        logger.info(f"Cargo reembolsado: {charge.id}")

        # Buscar pedido asociado
        try:
            payment_intent_id = charge.get('payment_intent')
            order = Order.objects.get(payment_id=payment_intent_id)

            # Determinar si es reembolso total o parcial
            if charge.get('amount_refunded') == charge.get('amount'):
                order.payment_status = 'refunded'
                order.status = 'CANCELLED'
            else:
                order.payment_status = 'partially_refunded'

            order.save()

            # Registrar cambio en historial
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                notes=_("Reembolso procesado por webhook")
            )

        except Order.DoesNotExist:
            logger.warning(f"No se encontró pedido para el cargo {charge.id}")
        except Exception as e:
            logger.error(f"Error al procesar reembolso: {str(e)}")