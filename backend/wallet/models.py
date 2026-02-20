from django.db import models
from django.conf import settings
import uuid

class Wallet(models.Model):
    """
    Wallet model - One wallet per user
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.business_name} - ₦{self.balance}"

    def credit(self, amount, description="", reference="", metadata=None):
        """Credit wallet and create transaction record"""
        self.balance += amount
        self.save()

        Transaction.objects.create(
            wallet=self,
            type='credit',
            amount=amount,
            description=description,
            reference=reference,
            balance_after=self.balance,
            status='completed',
            metadata=metadata
        )

        return self.balance

    def debit(self, amount, description="", reference="", metadata=None):
        """Debit wallet and create transaction record"""
        if self.balance < amount:
            raise ValueError("Insufficient wallet balance")

        self.balance -= amount
        self.save()

        Transaction.objects.create(
            wallet=self,
            type='debit',
            amount=amount,
            description=description,
            reference=reference,
            balance_after=self.balance,
            status='completed',
            metadata=metadata
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
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')

    # Transaction details
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, unique=True, db_index=True)

    # Balance tracking
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Paystack integration
    paystack_reference = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    paystack_status = models.CharField(max_length=50, null=True, blank=True)

    # Metadata
    metadata = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['wallet', '-created_at']),
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
        related_name='virtual_account'
    )
    account_number = models.CharField(max_length=20, unique=True, db_index=True)
    account_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100, default="Wema Bank")
    bank_code = models.CharField(max_length=10, default="000017")
    # ID returned by CoreBanking API for this virtual account
    corebanking_account_id = models.CharField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'virtual_accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.business_name} - {self.account_number} ({self.bank_name})"


class WebhookLog(models.Model):
    """
    WebhookLog model - Stores all incoming webhook calls for audit and debugging.
    Records are created BEFORE processing to ensure we never lose webhook data.
    """
    WEBHOOK_SOURCE_CHOICES = [
        ('corebanking', 'CoreBanking (LibertyPay)'),
        ('paystack', 'Paystack'),
    ]

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=20, choices=WEBHOOK_SOURCE_CHOICES, db_index=True)

    # Raw webhook data
    payload = models.JSONField(help_text="Complete webhook payload as received")
    headers = models.JSONField(null=True, blank=True, help_text="HTTP headers from webhook request")

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Processing results
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_logs',
        help_text="Transaction created from this webhook (if any)"
    )
    error_message = models.TextField(null=True, blank=True, help_text="Error message if processing failed")
    error_traceback = models.TextField(null=True, blank=True, help_text="Full error traceback for debugging")

    # Webhook metadata
    transaction_reference = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    recipient_account_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Signature verification
    signature_valid = models.BooleanField(null=True, blank=True)
    signature_received = models.CharField(max_length=255, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhook_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['source', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_reference']),
        ]

    def __str__(self):
        return f"{self.source.upper()} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def mark_processing(self):
        """Mark webhook as being processed"""
        from django.utils import timezone
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at', 'updated_at'])

    def mark_processed(self, transaction=None):
        """Mark webhook as successfully processed"""
        from django.utils import timezone
        self.status = 'processed'
        self.processing_completed_at = timezone.now()
        if transaction:
            self.transaction = transaction
        self.save(update_fields=['status', 'processing_completed_at', 'transaction', 'updated_at'])

    def mark_failed(self, error_message, error_traceback=None):
        """Mark webhook as failed with error details"""
        from django.utils import timezone
        self.status = 'failed'
        self.processing_completed_at = timezone.now()
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.save(update_fields=['status', 'processing_completed_at', 'error_message', 'error_traceback', 'updated_at'])

    def mark_skipped(self, reason):
        """Mark webhook as skipped with reason"""
        from django.utils import timezone
        self.status = 'skipped'
        self.processing_completed_at = timezone.now()
        self.error_message = reason
        self.save(update_fields=['status', 'processing_completed_at', 'error_message', 'updated_at'])
