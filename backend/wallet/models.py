from decimal import Decimal
import traceback
from django.db import models
from django.conf import settings
import uuid
import logging
from django.db import transaction as db_transaction

logger = logging.getLogger(__name__)


class Wallet(models.Model):
    """
    Wallet model - One wallet per user
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.business_name} - ₦{self.balance}"

    @db_transaction.atomic
    def credit(self, amount, description="", reference="", metadata=None):
        """Credit wallet and create transaction record"""
        # Lock the wallet row to prevent race conditions
        wallet = Wallet.objects.select_for_update().get(id=self.id)

        previous_balance = wallet.balance
        wallet.balance += amount
        wallet.save()

        # Update current instance to reflect the new balance
        self.balance = wallet.balance

        Transaction.objects.create(
            wallet=self,
            type="credit",
            amount=amount,
            description=description,
            reference=reference,
            balance_before=previous_balance,
            balance_after=self.balance,
            status="completed",
            metadata=metadata,
        )

        # Process pending charges after credit
        self.process_pending_charges()

        return self.balance

    def process_pending_charges(self):
        """Check for and process any pending charges for this user"""
        from .models import Charge  # Local import to be safe

        charges = Charge.objects.filter(
            user=self.user, status="pending", is_active=True
        ).order_by("-created_at")

        for charge in charges:
            if self.balance >= charge.amount:
                try:
                    with db_transaction.atomic():
                        # Use a more specific reference for the debit
                        debit_ref = f"CHRG-{charge.id.hex[:12].upper()}"

                        # Debit the wallet
                        self.debit(
                            amount=charge.amount,
                            description=f"Auto-debit for Order {charge.order.order_number}",
                            reference=debit_ref,
                            metadata={
                                "charge_id": str(charge.id),
                                "order_number": charge.order.order_number,
                            },
                        )

                        # Update charge status
                        charge.status = "completed"
                        charge.save()

                        # Update order payment status
                        order = charge.order
                        order.payment_status = "Paid"
                        order.save(update_fields=["payment_status"])
                        # also if order is relay order, update the sub_orders payment_status
                        if order.is_relay_order:
                            sub_orders = order.sub_orders.all()
                            for sub_order in sub_orders:
                                sub_order.payment_status = "Paid"
                                sub_order.save(update_fields=["payment_status"])

                        logger.info(
                            f"Auto-debited charge {charge.id} for order {order.order_number}"
                        )
                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Failed to auto-debit charge {charge.id}: {e}")
                    raise e
            else:
                logger.info("No charges found for the user")
                # Not enough balance to cover this charge, and since we order by created_at,
                # we might want to stop or continue to smaller charges.
                # For now, let's continue to see if smaller charges can be covered.
                continue

    @db_transaction.atomic
    def debit(self, amount, description="", reference="", metadata=None):
        """Debit wallet and create transaction record"""
        # Lock the wallet row to prevent race conditions
        wallet = Wallet.objects.select_for_update().get(id=self.id)

        if wallet.balance < amount:
            raise ValueError("Insufficient wallet balance")

        previous_balance = wallet.balance
        wallet.balance -= amount
        wallet.save()

        # Update current instance to reflect the new balance
        self.balance = wallet.balance

        Transaction.objects.create(
            wallet=self,
            type="debit",
            amount=amount,
            description=description,
            reference=reference,
            balance_before=previous_balance,
            balance_after=self.balance,
            status="completed",
            metadata=metadata,
        )

        return self.balance

    def can_debit(self, amount):
        """Check if wallet has sufficient balance"""
        return self.balance >= amount


class Transaction(models.Model):
    """
    Transaction model - Records all wallet transactions
    """

    TRANSACTION_TYPE_CHOICES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("reversed", "Reversed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )

    # Transaction details
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, unique=True, db_index=True)

    # Balance tracking
    balance_before = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Paystack integration
    paystack_reference = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    paystack_status = models.CharField(max_length=50, null=True, blank=True)

    # Metadata
    metadata = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["wallet", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.type.upper()} - ₦{self.amount} - {self.reference}"

    def save(self, *args, **kwargs):
        # Auto-generate reference if not provided
        if not self.reference:
            self.reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        # Set balance_before if not set
        if self.balance_before is None and self.wallet:
            self.balance_before = self.wallet.balance

        super().save(*args, **kwargs)


class VirtualAccount(models.Model):
    """
    VirtualAccount model - One Wema Bank virtual account per user (permanent)
    Created via CoreBanking (LibertyPay) API on first wallet funding via transfer.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="virtual_account",
    )
    account_number = models.CharField(max_length=20, unique=True, db_index=True)
    account_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100, default="Wema Bank")
    bank_code = models.CharField(max_length=10, default="000017")
    # ID returned by CoreBanking API for this virtual account
    corebanking_account_id = models.CharField(
        max_length=100, unique=True, db_index=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "virtual_accounts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.business_name} - {self.account_number} ({self.bank_name})"


class WebhookLog(models.Model):
    """
    WebhookLog model - Stores all incoming webhook calls for audit and debugging.
    Records are created BEFORE processing to ensure we never lose webhook data.
    """

    WEBHOOK_SOURCE_CHOICES = [
        ("corebanking", "CoreBanking (LibertyPay)"),
        ("paystack", "Paystack"),
    ]

    STATUS_CHOICES = [
        ("received", "Received"),
        ("processing", "Processing"),
        ("processed", "Processed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(
        max_length=20, choices=WEBHOOK_SOURCE_CHOICES, db_index=True
    )

    # Raw webhook data
    payload = models.JSONField(help_text="Complete webhook payload as received")
    headers = models.JSONField(
        null=True, blank=True, help_text="HTTP headers from webhook request"
    )

    # Processing status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="received", db_index=True
    )
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Processing results
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_logs",
        help_text="Transaction created from this webhook (if any)",
    )
    error_message = models.TextField(
        null=True, blank=True, help_text="Error message if processing failed"
    )
    error_traceback = models.TextField(
        null=True, blank=True, help_text="Full error traceback for debugging"
    )

    # Webhook metadata
    transaction_reference = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    recipient_account_number = models.CharField(
        max_length=20, null=True, blank=True, db_index=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Signature verification
    signature_valid = models.BooleanField(null=True, blank=True)
    signature_received = models.CharField(max_length=255, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhook_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["source", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["transaction_reference"]),
        ]

    def __str__(self):
        return f"{self.source.upper()} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def mark_processing(self):
        """Mark webhook as being processed"""
        from django.utils import timezone

        self.status = "processing"
        self.processing_started_at = timezone.now()
        self.save(update_fields=["status", "processing_started_at", "updated_at"])

    def mark_processed(self, transaction=None):
        """Mark webhook as successfully processed"""
        from django.utils import timezone

        self.status = "processed"
        self.processing_completed_at = timezone.now()
        if transaction:
            self.transaction = transaction
        self.save(
            update_fields=[
                "status",
                "processing_completed_at",
                "transaction",
                "updated_at",
            ]
        )

    def mark_failed(self, error_message, error_traceback=None):
        """Mark webhook as failed with error details"""
        from django.utils import timezone

        self.status = "failed"
        self.processing_completed_at = timezone.now()
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.save(
            update_fields=[
                "status",
                "processing_completed_at",
                "error_message",
                "error_traceback",
                "updated_at",
            ]
        )

    def mark_skipped(self, reason):
        """Mark webhook as skipped with reason"""
        from django.utils import timezone

        self.status = "skipped"
        self.processing_completed_at = timezone.now()
        self.error_message = reason
        self.save(
            update_fields=[
                "status",
                "processing_completed_at",
                "error_message",
                "updated_at",
            ]
        )


class Charge(models.Model):
    """
    Charge model - Tracks pending payments for orders.
    When a user hits 'pay-now', a charge is created.
    When the wallet is funded, pending charges are automatically debited.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="charges"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="charges"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "charges"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Charge {self.amount} for Order {self.order.order_number} ({self.status})"
        )


class AmortizationWallet(models.Model):
    """
    Locked wallet for Bike Hire Purchase / Amortization.
    Funds here can ONLY be moved to the Main Wallet.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="amortization_wallet",
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Immutable balance",
    )
    total_paid_to_date = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="This is the total paid to date locked",
    )
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="The cost of the amortized asset e.g Bike",
    )
    expected_daily_payment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Expected daily payment amount!",
    )

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "amortization_wallets"
        verbose_name = "Amortization Wallet"
        verbose_name_plural = "Amortization Wallets"

    def __str__(self) -> str:
        return f"{self.user.full_name} Amort Wallet"

    @property
    def ownership_percentage(self):
        if self.cost <= 0:
            return 0
        return (float(self.total_paid_to_date) / float(self.cost)) * 100

    @classmethod
    def create_one(cls, user: any) -> any:
        """Create one Amortization Wallet for a user"""
        if cls.objects.filter(user=user).exists():
            raise ValueError("Amortization wallet already exists for this user")
        daily_target = 8500  # 8500 per day for each rider
        cost = 470 * daily_target  # 8500 daily for 18 months excluding sundays
        return cls.objects.create(
            user=user, cost=cost, expected_daily_payment=daily_target
        )

    @db_transaction.atomic
    def credit(self, amount, ref, meta=None):
        wallet = AmortizationWallet.objects.select_for_update().get(id=self.id)
        prev_balance = self.balance
        new_balance = prev_balance + amount
        wallet.balance += amount
        wallet.total_paid_to_date += amount
        wallet.save()
        description = "Bike Hire Purchase payment"

        transaction = AmortizationTransaction.objects.create(
            amortization_wallet=wallet,
            entry_type="credit",
            amount=amount,
            balance_before=prev_balance,
            balance_after=new_balance,
            reference=ref,
            description=description,
            metadata=meta,
        )
        return transaction


class AmortizationTransaction(models.Model):
    """
    Dedicated ledger for Bike Hire Purchase payments. Immutable credit entry
    """

    ENTRY_TYPES = (("credit", "Credit"),)
    # Status
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    amortization_wallet = models.ForeignKey(
        AmortizationWallet, on_delete=models.CASCADE, related_name="ledger_entries"
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES, default="credit")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="success",
        help_text="Payment status from gateway",
    )

    # Webhook verification
    metadata = models.JSONField(null=True, blank=True)
    webhook_received_at = models.DateTimeField(null=True, blank=True)
    webhook_verified_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "amortization_transactions"
        ordering = ["-created_at"]
        verbose_name = "Amortization Ledger Entry"
        verbose_name_plural = "Amortization Ledger Entries"


class AmortizationVirtualAccount(models.Model):
    """
    Represents a virtual bank account assigned to a rider amort wallet
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="amort_virtual_account",
    )
    account_number = models.CharField(max_length=20, unique=True, db_index=True)
    account_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100, default="Wema Bank")
    bank_code = models.CharField(max_length=10, default="000017")
    # ID returned by CoreBanking API for this virtual account
    corebanking_account_id = models.CharField(
        max_length=100, unique=True, db_index=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} Amort Virtual Account"
