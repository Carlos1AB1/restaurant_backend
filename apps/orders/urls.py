from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, OrderViewSet

# Router para Carrito (no es un ModelViewSet típico)
cart_router = DefaultRouter()
cart_router.register(r'cart', CartViewSet, basename='cart')

# Router para Pedidos
order_router = DefaultRouter()
order_router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(cart_router.urls)),
    path('', include(order_router.urls)),
    # Las URLs específicas (@action) se generan automáticamente por los routers.
    # Ej: /api/orders/cart/my-cart/
    # Ej: /api/orders/orders/{pk}/cancel/
    # Ej: /api/orders/orders/{pk}/update-status/
]