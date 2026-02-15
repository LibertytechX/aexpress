from django.contrib import admin
from .models import Wallet, Transaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'created_at', 'updated_at']
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
