from django.urls import path
from .views import WebhookCreateUpdateView

urlpatterns = [
    path("config/", WebhookCreateUpdateView.as_view(), name="webhook-config"),
]
