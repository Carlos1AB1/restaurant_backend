import stripe
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

# Configurar stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Configurar logger
logger = logging.getLogger(__name__)


class StripeService:
    """
    Servicio para procesar pagos con Stripe.
    """

    @staticmethod
    def create_payment_intent(order):
        """
        Crea un intento de pago en Stripe para un pedido.

        Args:
            order: Instancia del modelo Order

        Returns:
            dict: Datos del intento de pago con client_secret para completar en el frontend
        """
        try:
            # Convertir precio a centavos (Stripe usa la moneda menor, ej. centavos para USD)
            amount = int(order.total * 100)

            # Crear intento de pago
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="mxn",  # Moneda (ajustar según región)
                description=f"Pedido #{order.order_number}",
                metadata={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "user_id": str(order.user.id),
                    "user_email": order.user.email
                }
            )

            # Actualizar pedido con ID de pago
            order.payment_id = payment_intent.id
            order.payment_status = "pending"
            order.save()

            logger.info(f"Intento de pago creado para pedido #{order.order_number}: {payment_intent.id}")

            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error al crear intento de pago para pedido #{order.order_number}: {str(e)}")
            raise ValueError(_("Error al procesar el pago: {}").format(str(e)))

    @staticmethod
    def confirm_payment(payment_intent_id):
        """
        Confirma un pago en Stripe.

        Args:
            payment_intent_id: ID del intento de pago en Stripe

        Returns:
            bool: True si el pago fue exitoso
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == "succeeded":
                logger.info(f"Pago confirmado para intento {payment_intent_id}")
                return True

            logger.warning(
                f"Estado de pago no es 'succeeded' para intento {payment_intent_id}: {payment_intent.status}")
            return False

        except stripe.error.StripeError as e:
            logger.error(f"Error al confirmar pago {payment_intent_id}: {str(e)}")
            raise ValueError(_("Error al confirmar el pago: {}").format(str(e)))

    @staticmethod
    def refund_payment(payment_intent_id, amount=None):
        """
        Reembolsa un pago en Stripe.

        Args:
            payment_intent_id: ID del intento de pago en Stripe
            amount: Monto a reembolsar en centavos (opcional, si no se especifica se reembolsa todo)

        Returns:
            dict: Datos del reembolso
        """
        try:
            if amount:
                refund = stripe.Refund.create(
                    payment_intent=payment_intent_id,
                    amount=amount
                )
            else:
                refund = stripe.Refund.create(
                    payment_intent=payment_intent_id
                )

            logger.info(f"Reembolso creado para intento {payment_intent_id}: {refund.id}")

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error al reembolsar pago {payment_intent_id}: {str(e)}")
            raise ValueError(_("Error al procesar el reembolso: {}").format(str(e)))

    @staticmethod
    def process_webhook(payload, signature):
        """
        Procesa un webhook de Stripe.

        Args:
            payload: Datos del webhook
            signature: Firma del webhook

        Returns:
            dict: Evento procesado
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )

            logger.info(f"Webhook recibido: {event.type}")

            return event

        except ValueError as e:
            # Invalid payload
            logger.error(f"Error en payload de webhook: {str(e)}")
            raise

        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Error en firma de webhook: {str(e)}")
            raise