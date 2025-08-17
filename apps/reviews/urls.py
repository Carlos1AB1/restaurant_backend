from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    # URLs para acciones como approve/unapprove se generan automáticamente:
    # /api/reviews/reviews/{pk}/approve/
    # /api/reviews/reviews/{pk}/unapprove/
]