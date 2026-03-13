import json
import asyncio
import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
)

logger = logging.getLogger(__name__)


def _publish_to_ably(channel_name: str, event: str, data: dict):
    """Publish a message to an Ably channel using the REST client."""
    api_key = getattr(settings, "ABLY_API_KEY", "")
    if not api_key:
        logger.warning("chats: ABLY_API_KEY not configured, skipping publish")
        return

    async def _publish():
        from ably import AblyRest

        client = AblyRest(api_key)
        channel = client.channels.get(channel_name)
        await channel.publish(event, data)

    try:
        asyncio.run(_publish())
    except Exception as exc:
        logger.error("chats: Ably publish failed for channel %s: %s", channel_name, exc)


class ConversationListView(generics.ListAPIView):
    """
    GET /api/chats/conversations/
    Dispatcher-facing sidebar: all conversations ordered by most recent activity.
    Uses denormalized last_message + unread_count — no annotation overhead.
    """

    serializer_class = ConversationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Conversation.objects.select_related("user_id").order_by("-updated_at")

        # Optional filters
        convo_type = self.request.query_params.get("type")  # customer | rider
        if convo_type:
            qs = qs.filter(type=convo_type)

        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ("true", "1"))

        return qs


class ConversationCreateOrGetView(APIView):
    """
    POST /api/chats/conversations/
    Customer/Rider: open a support conversation (or return the existing active one).
    The participant_type is derived from the authenticated user's usertype.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_type = user.usertype.lower()  # e.g. "customer", "rider"

        if user_type not in ("customer", "rider"):
            return Response(
                {"error": "Only customers and riders can open a conversation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Return existing active conversation or create a new one
        conversation, created = Conversation.objects.get_or_create(
            user_id=user,
            type=user_type,
            is_active=True,
            defaults={"last_message": "", "unread_count": 0},
        )

        serializer = ConversationListSerializer(conversation)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MessageListView(generics.ListAPIView):
    """
    GET /api/chats/conversations/<pk>/messages/
    Returns paginated message history for a conversation.
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_pk = self.kwargs["pk"]
        return Message.objects.filter(conversation_id=conversation_pk).order_by(
            "timestamp"
        )


class SendMessageView(APIView):
    """
    POST /api/chats/conversations/<pk>/messages/
    Both agents and users (customer/rider) can send here.

    On success:
    1. Saves the Message to DB.
    2. Updates Conversation.last_message + unread_count (denormalized).
    3. Publishes to the Ably channel so the other party receives it in real time.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.select_related("user_id").get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"error": "content is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Determine sender_type from the authenticated user
        user = request.user
        if user == conversation.user_id:
            sender_type = conversation.type  # "customer" or "rider"
        else:
            # Treat anyone else (dispatcher / admin) as agent
            sender_type = "agent"

        message = Message.objects.create(
            conversation=conversation,
            sender_type=sender_type,
            content=content,
        )

        # Update denormalized fields on Conversation
        # Agents sending increments nothing; user messages increment unread_count for agent
        if sender_type != "agent":
            Conversation.objects.filter(pk=pk).update(
                last_message=content,
                unread_count=conversation.unread_count + 1,
            )
        else:
            Conversation.objects.filter(pk=pk).update(last_message=content)

        # Refresh updated_at (auto_now fires on save, not update())
        conversation.save(update_fields=["updated_at"])

        # Publish real-time event via Ably REST
        payload = {
            "id": str(message.id),
            "conversation_id": str(conversation.id),
            "sender_type": sender_type,
            "content": content,
            "timestamp": message.timestamp.isoformat(),
        }
        _publish_to_ably(conversation.ably_channel_name, "new_message", payload)

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MarkReadView(APIView):
    """
    POST /api/chats/conversations/<pk>/read/
    Agent marks all unread messages in this conversation as read and resets unread_count to 0.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = Message.objects.filter(conversation_id=pk, is_read=False).update(
            is_read=True
        )

        Conversation.objects.filter(pk=pk).update(unread_count=0)

        return Response({"marked_read": updated})
