from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["id", "sender_type", "content", "is_read", "timestamp"]
    can_delete = False
    ordering = ["timestamp"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "type",
        "user_id",
        "last_message_preview",
        "unread_count",
        "is_active",
        "updated_at",
    ]
    list_filter = ["type", "is_active"]
    search_fields = ["user_id__phone", "user_id__email", "user_id__first_name", "last_message"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [MessageInline]
    ordering = ["-updated_at"]

    def last_message_preview(self, obj):
        return obj.last_message[:60] if obj.last_message else "—"

    last_message_preview.short_description = "Last Message"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender_type", "content_preview", "is_read", "timestamp"]
    list_filter = ["sender_type", "is_read"]
    search_fields = ["content", "conversation__user_id__phone"]
    readonly_fields = ["id", "timestamp"]
    ordering = ["-timestamp"]

    def content_preview(self, obj):
        return obj.content[:60]

    content_preview.short_description = "Content"
