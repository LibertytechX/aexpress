from django.contrib import admin
from .models import Webhook, WebhookOutbox

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('event_name', 'url')
    ordering = ('event_name',)

@admin.register(WebhookOutbox)
class WebhookOutboxAdmin(admin.ModelAdmin):
    list_display = ('id', 'webhook', 'status', 'retry_count', 'last_attempt_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('webhook__event_name', 'payload', 'error_message')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')
