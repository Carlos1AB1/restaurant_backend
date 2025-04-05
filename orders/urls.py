from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CartView,
    CartItemViewSet,
    OrderViewSet,
    CheckoutView
)

# Crear router para ViewSets
router = DefaultRouter()
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]