from django.urls import path
from .views import test_send_whatsapp, test_whatsapp_info

urlpatterns = [
    path('test-send/', test_send_whatsapp, name='test-send-whatsapp'),
    path('test-info/', test_whatsapp_info, name='test-whatsapp-info'),
]
