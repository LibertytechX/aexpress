import uuid
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    A support chat thread between a user (customer or rider) and the support team.

    `last_message` and `unread_count` are denormalized for fast sidebar queries —
    no JOIN or annotation needed when listing conversations.
    """

    TYPE_CHOICES = (
        ("customers", "Customers"),
        ("riders", "Riders"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations",
        db_column="user_id",
    )
    # Denormalized fields — kept in sync by SendMessageView
    last_message = models.TextField(blank=True, default="")
    unread_count = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_conversations"
        ordering = ["-updated_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"[{self.type}] {self.user_id} — {self.last_message[:40]}"

    @property
    def ably_channel_name(self):
        return f"chat:{self.type}:{self.user_id_id}"


class Message(models.Model):
    """
    A single message within a Conversation.
    sender_type distinguishes who sent it: the user (customer/rider) or the agent.
    """

    SENDER_TYPE_CHOICES = (
        ("agent", "agent"),
        ("customer", "customer"),
        ("rider", "rider"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["timestamp"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"[{self.sender_type}] {self.content[:60]}"
