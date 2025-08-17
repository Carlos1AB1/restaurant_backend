from django.urls import path
from .views import ContactMessageCreateView
# from .views import ContactMessageViewSet # Si añades el ViewSet
# from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register(r'messages', ContactMessageViewSet) # Si usas ViewSet para admins

urlpatterns = [
    path('send-message/', ContactMessageCreateView.as_view(), name='contact-send'),
    # path('admin/', include(router.urls)), # Si usas ViewSet para admins
]