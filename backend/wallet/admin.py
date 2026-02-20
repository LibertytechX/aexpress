from django.contrib import admin
from .models import Wallet, Transaction, VirtualAccount, WebhookLog

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'virtual_account_number', 'created_at', 'updated_at']
    search_fields = ['user__business_name', 'user__phone', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_filter = ['created_at']

    fieldsets = (
        ('Wallet Information', {
            'fields': ('id', 'user', 'balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def virtual_account_number(self, obj):
        """Display the associated virtual account number if it exists."""
        try:
            return obj.user.virtual_account.account_number
        except VirtualAccount.DoesNotExist:
            return "N/A"
    virtual_account_number.short_description = 'Virtual Account'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'wallet', 'type', 'amount', 'status', 'created_at']
    search_fields = ['reference', 'paystack_reference', 'description', 'wallet__user__business_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_filter = ['type', 'status', 'created_at']

    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'wallet', 'type', 'amount', 'description', 'reference')
        }),
        ('Balance Tracking', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Paystack Integration', {
            'fields': ('paystack_reference', 'paystack_status')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    """Admin configuration for VirtualAccount model."""

    list_display = ['user', 'account_number', 'account_name', 'bank_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'bank_name', 'created_at']
    search_fields = ['user__business_name', 'user__phone', 'user__email', 'account_number', 'account_name']
    readonly_fields = ['id', 'account_number', 'corebanking_account_id', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('id', 'user')
        }),
        ('Account Details', {
            'fields': ('account_number', 'account_name', 'bank_name', 'bank_code')
        }),
        ('CoreBanking Integration', {
            'fields': ('corebanking_account_id', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Admin configuration for WebhookLog model."""

    list_display = ['created_at', 'source', 'status', 'transaction_reference', 'amount', 'recipient_account_number', 'signature_valid']
    list_filter = ['source', 'status', 'signature_valid', 'created_at']
    search_fields = ['transaction_reference', 'recipient_account_number', 'error_message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processing_started_at', 'processing_completed_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Webhook Information', {
            'fields': ('id', 'source', 'status', 'created_at', 'updated_at')
        }),
        ('Processing Timeline', {
            'fields': ('processing_started_at', 'processing_completed_at')
        }),
        ('Webhook Data', {
            'fields': ('payload', 'headers')
        }),
        ('Extracted Metadata', {
            'fields': ('transaction_reference', 'recipient_account_number', 'amount')
        }),
        ('Signature Verification', {
            'fields': ('signature_valid', 'signature_received')
        }),
        ('Processing Results', {
            'fields': ('transaction', 'error_message', 'error_traceback')
        }),
    )

    def has_add_permission(self, request):
        """Disable manual creation of webhook logs"""
        return False
