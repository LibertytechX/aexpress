from django.urls import path
from .views import (
    SupportTicketCreateView,
    SupportTicketListView,
    SupportTicketDetailView,
    whisper360_webhook,
)

app_name = "support"

urlpatterns = [
    path("", SupportTicketCreateView.as_view(), name="ticket-create"),
    path("tickets/", SupportTicketListView.as_view(), name="ticket-list"),
    path(
        "tickets/<str:reference>/",
        SupportTicketDetailView.as_view(),
        name="ticket-detail",
    ),
    path(
        "whisper360/webhook/",
        whisper360_webhook,
        name="whisper360-webhook",
    ),
]
