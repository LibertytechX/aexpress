from django.contrib import admin
from .models import Wallet, Transaction, VirtualAccount, WebhookLog, Charge


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "balance",
        "virtual_account_number",
        "created_at",
        "updated_at",
    ]
    search_fields = ["user__business_name", "user__phone", "user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_filter = ["created_at"]
    actions = ["settle_pending_charges"]

    fieldsets = (
        ("Wallet Information", {"fields": ("id", "user", "balance")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Settle pending charges for selected wallets")
    def settle_pending_charges(self, request, queryset):
        """Settle pending charges for the selected wallets."""
        from django.contrib import messages
        import traceback
        import logging

        logger = logging.getLogger(__name__)
        success_count = 0
        error_count = 0

        for wallet in queryset:
            try:
                wallet.process_pending_charges()
                success_count += 1
            except Exception as e:
                error_count += 1
                print("hit an error!")
                logger.error(f"Error settling charges for wallet {wallet.id}: {e}")
                logger.error(traceback.format_exc())
                self.message_user(
                    request,
                    f"Error settling charges for {wallet.user.business_name}: {str(e)}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully triggered charge settlement for {success_count} wallets.",
            )

    def virtual_account_number(self, obj):
        """Display the associated virtual account number if it exists."""
        try:
            return obj.user.virtual_account.account_number
        except VirtualAccount.DoesNotExist:
            return "N/A"

    virtual_account_number.short_description = "Virtual Account"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "wallet",
        "type",
        "amount",
        "balance_before",
        "balance_after",
        "status",
        "created_at",
    ]
    search_fields = [
        "reference",
        "paystack_reference",
        "description",
        "wallet__user__business_name",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_filter = ["type", "status", "created_at", "wallet"]

    fieldsets = (
        (
            "Transaction Information",
            {"fields": ("id", "wallet", "type", "amount", "description", "reference")},
        ),
        ("Balance Tracking", {"fields": ("balance_before", "balance_after")}),
        ("Status", {"fields": ("status",)}),
        ("Paystack Integration", {"fields": ("paystack_reference", "paystack_status")}),
        ("Metadata", {"fields": ("metadata",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    """Admin configuration for VirtualAccount model."""

    list_display = [
        "user",
        "account_number",
        "account_name",
        "bank_name",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "bank_name", "created_at"]
    search_fields = [
        "user__business_name",
        "user__phone",
        "user__email",
        "account_number",
        "account_name",
    ]
    readonly_fields = ["id", "account_number", "corebanking_account_id", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("User Information", {"fields": ("id", "user")}),
        (
            "Account Details",
            {"fields": ("account_number", "account_name", "bank_name", "bank_code")},
        ),
        (
            "CoreBanking Integration",
            {"fields": ("corebanking_account_id", "is_active")},
        ),
        ("Timestamps", {"fields": ("created_at",)}),
    )


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    """Admin configuration for WebhookLog model."""

    list_display = [
        "created_at",
        "source",
        "status",
        "transaction_reference",
        "amount",
        "recipient_account_number",
        "signature_valid",
    ]
    list_filter = ["source", "status", "signature_valid", "created_at"]
    search_fields = [
        "transaction_reference",
        "recipient_account_number",
        "error_message",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "processing_started_at",
        "processing_completed_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Webhook Information",
            {"fields": ("id", "source", "status", "created_at", "updated_at")},
        ),
        (
            "Processing Timeline",
            {"fields": ("processing_started_at", "processing_completed_at")},
        ),
        ("Webhook Data", {"fields": ("payload", "headers")}),
        (
            "Extracted Metadata",
            {"fields": ("transaction_reference", "recipient_account_number", "amount")},
        ),
        (
            "Signature Verification",
            {"fields": ("signature_valid", "signature_received")},
        ),
        (
            "Processing Results",
            {"fields": ("transaction", "error_message", "error_traceback")},
        ),
    )

    def has_add_permission(self, request):
        """Disable manual creation of webhook logs"""
        return False


@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "order",
        "amount",
        "status",
        "is_active",
        "created_at",
    ]
    list_filter = ["status", "is_active", "created_at", "user"]
    search_fields = [
        "user__email",
        "user__phone",
        "user__business_name",
        "order__order_number",
        "id",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    actions = ["debit_and_complete_charge", "soft_delete_charges"]

    fieldsets = (
        (
            "Charge Information",
            {"fields": ("id", "user", "order", "amount", "status", "is_active")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Soft delete selected charges")
    def soft_delete_charges(self, request, queryset):
        """Deactivate selected charges."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully deactivated {updated} charges.",
        )

    @admin.action(description="Debit wallet, complete charge, and set order to paid")
    def debit_and_complete_charge(self, request, queryset):
        from django.contrib import messages
        from django.db import transaction as db_transaction
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        success_count = 0
        error_count = 0

        for charge in queryset:
            if charge.status == "completed":
                self.message_user(
                    request,
                    f"Charge {charge.id} is already completed. Skipping.",
                    level=messages.WARNING,
                )
                continue

            try:
                wallet = charge.user.wallet

                with db_transaction.atomic():
                    # Debit the wallet
                    debit_ref = f"CHRG-ADM-{charge.id.hex[:10].upper()}"
                    wallet.debit(
                        amount=charge.amount,
                        description=f"Admin manual debit for Order {charge.order.order_number}",
                        reference=debit_ref,
                        metadata={
                            "charge_id": str(charge.id),
                            "order_number": charge.order.order_number,
                            "admin_action": True,
                        },
                    )

                    # Update charge status
                    charge.status = "completed"
                    charge.save()

                    # Update order payment status
                    order = charge.order
                    order.payment_status = "Paid"
                    order.save(update_fields=["payment_status"])

                    success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to manually direct debit charge {charge.id}: {e}")
                logger.error(traceback.format_exc())
                self.message_user(
                    request,
                    f"Error processing charge {charge.id} for {charge.user.business_name}: {str(e)} - {wallet.balance}",
                    level=messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully debited and completed {success_count} charges.",
                level=messages.SUCCESS,
            )
