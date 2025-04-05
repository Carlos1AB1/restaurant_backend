from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ConversationViewSet,
    ChatMessageAPIView,
    ResetConversationAPIView,
    IntentViewSet,
    RecommendationLogListView
)

# Crear router para ViewSets
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'intents', IntentViewSet, basename='intent')

urlpatterns = [
    path('', include(router.urls)),
    path('message/', ChatMessageAPIView.as_view(), name='chat-message'),
    path('reset/', ResetConversationAPIView.as_view(), name='reset-conversation'),
    path('recommendations/', RecommendationLogListView.as_view(), name='recommendations'),
]