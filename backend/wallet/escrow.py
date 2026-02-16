"""
Escrow Management System for AX Merchant Portal

This module handles escrow operations for order payments:
- Hold funds when order is placed
- Release funds when delivery is completed
- Refund funds when order is canceled
- Handle partial refunds for multi-drop orders
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Wallet, Transaction


class EscrowManager:
    """Manages escrow operations for order payments."""

    @staticmethod
    @transaction.atomic
    def hold_funds(wallet, amount, order_number, description=""):
        """
        Hold funds in escrow when order is placed.

        This creates a DEBIT transaction that immediately deducts from the wallet.
        The transaction is marked as 'completed' (not pending) because the debit
        actually happened. The metadata tracks that it's held in escrow and can be refunded.

        Args:
            wallet: Wallet instance
            amount: Amount to hold (Decimal)
            order_number: Order number for reference
            description: Transaction description

        Returns:
            Transaction instance (escrow hold transaction)

        Raises:
            ValueError: If insufficient balance
        """
        if not wallet.can_debit(amount):
            raise ValueError(f"Insufficient balance. Required: ₦{amount}, Available: ₦{wallet.balance}")

        # Deduct from available balance
        balance_before = wallet.balance
        wallet.balance -= amount
        wallet.save()

        # Create escrow hold transaction (DEBIT - money leaves wallet)
        escrow_transaction = Transaction.objects.create(
            wallet=wallet,
            type='debit',
            amount=amount,
            description=description or f'Payment for order #{order_number} (held in escrow)',
            reference=f'ORDER-{order_number}',  # Changed to ORDER- for clarity
            balance_before=balance_before,
            balance_after=wallet.balance,
            status='completed',  # Completed because debit actually happened
            metadata={
                'escrow_status': 'held',
                'order_number': order_number,
                'can_refund': True,
                'is_escrow': True
            }
        )

        return escrow_transaction

    @staticmethod
    @transaction.atomic
    def release_funds(order_number, description=""):
        """
        Release escrowed funds when delivery is completed.
        Marks the escrow transaction as completed.

        Args:
            order_number: Order number
            description: Release description

        Returns:
            Transaction instance (updated escrow transaction)

        Raises:
            ValueError: If escrow transaction not found or already released
        """
        try:
            escrow_transaction = Transaction.objects.get(
                reference=f'ORDER-{order_number}',
                type='debit',
                status='completed',
                metadata__is_escrow=True,
                metadata__escrow_status='held'
            )
        except Transaction.DoesNotExist:
            raise ValueError(f"No held escrow found for order #{order_number}")

        # Mark escrow as released (cannot be refunded anymore)
        # No wallet balance change - money was already debited
        escrow_transaction.metadata['escrow_status'] = 'released'
        escrow_transaction.metadata['can_refund'] = False
        escrow_transaction.metadata['released_at'] = timezone.now().isoformat()
        if description:
            escrow_transaction.metadata['release_note'] = description
        escrow_transaction.save()

        return escrow_transaction

    @staticmethod
    @transaction.atomic
    def refund_funds(order_number, reason="", partial_amount=None):
        """
        Refund escrowed funds when order is canceled.

        Args:
            order_number: Order number
            reason: Refund reason
            partial_amount: Amount to refund (None = full refund)

        Returns:
            tuple: (escrow_transaction, refund_transaction)

        Raises:
            ValueError: If escrow transaction not found or cannot be refunded
        """
        try:
            escrow_transaction = Transaction.objects.get(
                reference=f'ORDER-{order_number}',
                type='debit',
                status='completed',
                metadata__is_escrow=True,
                metadata__can_refund=True
            )
        except Transaction.DoesNotExist:
            raise ValueError(f"No refundable escrow found for order #{order_number}")

        wallet = escrow_transaction.wallet
        refund_amount = partial_amount or escrow_transaction.amount

        # Validate partial refund
        if partial_amount and partial_amount > escrow_transaction.amount:
            raise ValueError(f"Partial refund amount (₦{partial_amount}) exceeds escrowed amount (₦{escrow_transaction.amount})")

        # Credit wallet with refund (CREDIT transaction - money returns)
        balance_before = wallet.balance
        wallet.balance += refund_amount
        wallet.save()

        # Create refund transaction (CREDIT - money back to wallet)
        refund_transaction = Transaction.objects.create(
            wallet=wallet,
            type='credit',
            amount=refund_amount,
            description=reason or f'Refund for canceled order #{order_number}',
            reference=f'REFUND-{order_number}',
            balance_before=balance_before,
            balance_after=wallet.balance,
            status='completed',
            metadata={
                'escrow_status': 'refunded',
                'order_number': order_number,
                'original_order_ref': f'ORDER-{order_number}',
                'refund_type': 'partial' if partial_amount else 'full',
                'is_escrow_refund': True
            }
        )

        # Update original escrow transaction metadata
        if partial_amount and partial_amount < escrow_transaction.amount:
            # Partial refund - mark partial refund but keep can_refund=True
            escrow_transaction.metadata['partial_refund'] = float(partial_amount)
            escrow_transaction.metadata['remaining_escrow'] = float(escrow_transaction.amount - partial_amount)
            escrow_transaction.metadata['refunded_at'] = timezone.now().isoformat()
            escrow_transaction.save()
        else:
            # Full refund - mark as fully refunded
            escrow_transaction.metadata['escrow_status'] = 'refunded'
            escrow_transaction.metadata['can_refund'] = False
            escrow_transaction.metadata['refunded_at'] = timezone.now().isoformat()
            escrow_transaction.save()

        return escrow_transaction, refund_transaction

    @staticmethod
    def get_escrow_status(order_number):
        """
        Get the current escrow status for an order.

        Args:
            order_number: Order number

        Returns:
            dict: Escrow status information
        """
        try:
            escrow_transaction = Transaction.objects.get(
                reference=f'ORDER-{order_number}',
                type='debit',
                metadata__is_escrow=True
            )

            return {
                'exists': True,
                'status': escrow_transaction.status,
                'amount': float(escrow_transaction.amount),
                'escrow_status': escrow_transaction.metadata.get('escrow_status', 'unknown'),
                'can_refund': escrow_transaction.metadata.get('can_refund', False),
                'created_at': escrow_transaction.created_at.isoformat(),
                'metadata': escrow_transaction.metadata
            }
        except Transaction.DoesNotExist:
            return {
                'exists': False,
                'status': None,
                'amount': 0,
                'escrow_status': 'not_found',
                'can_refund': False
            }

    @staticmethod
    def get_total_escrowed(wallet):
        """
        Get total amount currently held in escrow for a wallet.

        Args:
            wallet: Wallet instance

        Returns:
            Decimal: Total escrowed amount
        """
        held_escrows = Transaction.objects.filter(
            wallet=wallet,
            type='debit',
            status='completed',
            metadata__is_escrow=True,
            metadata__escrow_status='held',
            metadata__can_refund=True
        )

        total = sum(txn.amount for txn in held_escrows)
        return Decimal(str(total))

    @staticmethod
    def get_available_balance(wallet):
        """
        Get available balance (wallet balance - escrowed funds).

        Args:
            wallet: Wallet instance

        Returns:
            Decimal: Available balance
        """
        # Note: Since we already deduct from wallet.balance when holding escrow,
        # the wallet.balance already represents available balance
        return wallet.balance

    @staticmethod
    def get_escrow_history(wallet, status_filter=None):
        """
        Get escrow transaction history for a wallet.

        Args:
            wallet: Wallet instance
            status_filter: Optional filter by escrow_status ('held', 'released', 'refunded')

        Returns:
            QuerySet: Escrow transactions (debit transactions only)
        """
        from wallet.models import Transaction

        escrow_txns = Transaction.objects.filter(
            wallet=wallet,
            type='debit',
            metadata__is_escrow=True
        ).order_by('-created_at')

        if status_filter:
            escrow_txns = escrow_txns.filter(metadata__escrow_status=status_filter)

        return escrow_txns

    @staticmethod
    def get_completed_escrow_transactions(wallet):
        """
        Get all completed escrow transactions (funds that were held and released).

        Args:
            wallet: Wallet instance

        Returns:
            QuerySet: Completed escrow transactions
        """
        from wallet.models import Transaction

        return Transaction.objects.filter(
            wallet=wallet,
            type='debit',
            status='completed',
            metadata__is_escrow=True,
            metadata__escrow_status='released'
        ).order_by('-created_at')

    @staticmethod
    def get_refunded_escrow_transactions(wallet):
        """
        Get all refunded escrow transactions (funds that were held and refunded).

        Args:
            wallet: Wallet instance

        Returns:
            QuerySet: Refunded escrow transactions
        """
        from wallet.models import Transaction

        return Transaction.objects.filter(
            wallet=wallet,
            type='debit',
            status='completed',
            metadata__is_escrow=True,
            metadata__escrow_status='refunded'
        ).order_by('-created_at')

