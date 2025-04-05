from django.urls import path

from .views import (
    CreatePaymentIntentView,
    ConfirmPaymentView,
    RefundPaymentView,
    StripeWebhookView
)

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('confirm-payment/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    path('refund-payment/', RefundPaymentView.as_view(), name='refund-payment'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]