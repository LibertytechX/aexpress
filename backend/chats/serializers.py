from rest_framework import serializers
from .models import Conversation, Message
from authentication.models import User


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "sender_type", "content", "is_read", "timestamp"]
        read_only_fields = ["id", "conversation", "sender_type", "is_read", "timestamp"]


class ParticipantSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "phone"]

    def get_name(self, obj):
        return obj.get_full_name() or obj.phone


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the dispatcher sidebar.
    All expensive fields (last_message, unread_count) are already stored on the row.
    """

    participant = ParticipantSerializer(source="user_id", read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "participant",
            "last_message",
            "unread_count",
            "is_active",
            "updated_at",
            "created_at",
        ]


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Full conversation with message history."""

    participant = ParticipantSerializer(source="user_id", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "participant",
            "last_message",
            "unread_count",
            "is_active",
            "updated_at",
            "created_at",
            "messages",
        ]
