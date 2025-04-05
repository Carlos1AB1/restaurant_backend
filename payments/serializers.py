from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from orders.models import Order


class PaymentIntentCreateSerializer(serializers.Serializer):
    """
    Serializer para crear un intento de pago.
    """
    order_id = serializers.UUIDField(required=True)

    def validate_order_id(self, value):
        """Validar que el pedido existe."""
        try:
            Order.objects.get(id=value)
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError(_("El pedido no existe."))


class PaymentConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar un pago.
    """
    payment_intent_id = serializers.CharField(required=True)
    order_id = serializers.UUIDField(required=True)

    def validate(self, attrs):
        """Validar que el pedido existe y el payment_intent_id coincide."""
        try:
            order = Order.objects.get(id=attrs['order_id'])

            if order.payment_id != attrs['payment_intent_id']:
                raise serializers.ValidationError({
                    "payment_intent_id": _("El ID de pago no coincide con el del pedido.")
                })

            return attrs
        except Order.DoesNotExist:
            raise serializers.ValidationError({
                "order_id": _("El pedido no existe.")
            })


class PaymentRefundSerializer(serializers.Serializer):
    """
    Serializer para reembolsar un pago.
    """
    order_id = serializers.UUIDField(required=True)
    amount = serializers.IntegerField(required=False, min_value=1)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate_order_id(self, value):
        """Validar que el pedido existe y ha sido pagado."""
        try:
            order = Order.objects.get(id=value)

            if order.payment_status != 'completed':
                raise serializers.ValidationError(_("Solo se pueden reembolsar pedidos pagados."))

            if not order.payment_id:
                raise serializers.ValidationError(_("Este pedido no tiene un ID de pago asociado."))

            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError(_("El pedido no existe."))

    def validate_amount(self, value):
        """
        Validar que el monto a reembolsar es válido.
        El monto debe estar en centavos (ej. 1000 para $10.00).
        """
        if value <= 0:
            raise serializers.ValidationError(_("El monto a reembolsar debe ser mayor que cero."))
        return value