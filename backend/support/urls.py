from django.urls import path
from .views import (
    SupportTicketCreateView,
    SupportTicketListView,
    SupportTicketDetailView,
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
]
