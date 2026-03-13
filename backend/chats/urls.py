from django.urls import path
from .views import (
    ConversationListView,
    ConversationCreateOrGetView,
    MessageListView,
    SendMessageView,
    MarkReadView,
)

app_name = "chats"

urlpatterns = [
    # Dispatcher: list all conversations
    # Customer/Rider: open or retrieve their support conversation
    path("conversations/", ConversationListView.as_view(), name="conversation_list"),
    path("conversations/start/", ConversationCreateOrGetView.as_view(), name="conversation_start"),
    # Message history
    path(
        "conversations/<uuid:pk>/messages/",
        MessageListView.as_view(),
        name="message_list",
    ),
    # Send a message (agent or user)
    path(
        "conversations/<uuid:pk>/messages/send/",
        SendMessageView.as_view(),
        name="send_message",
    ),
    # Mark all messages as read
    path(
        "conversations/<uuid:pk>/read/",
        MarkReadView.as_view(),
        name="mark_read",
    ),
]
