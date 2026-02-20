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
