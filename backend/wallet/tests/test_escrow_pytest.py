from decimal import Decimal
import pytest
from test_utils.helpers import TestCaseHelper
from test_utils.factories.wallet import WalletFactory
from wallet.escrow import EscrowManager
from wallet.models import Transaction


@pytest.mark.django_db
class TestEscrowSystem(TestCaseHelper):
    """
    Test suite for the AExpress Escrow Management System.
    """

    def setup_method(self):
        super().setup_method()
        self.wallet = WalletFactory(balance=Decimal("10000.00"))
        self.wallet.balance = Decimal("10000.00")
        self.wallet.save()
        self.order_number = "6158001"
        self.hold_amount = Decimal("3000.00")

    def test_hold_funds_success(self):
        """
        Verify that holding funds successfully debits the wallet and creates
        an escrow transaction with status 'completed' and 'held' metadata.
        """
        initial_balance = self.wallet.balance

        # Hold funds
        escrow_txn = EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number,
            description="Holding payment for order"
        )

        # Assertions
        assert self.wallet.balance == initial_balance - self.hold_amount
        assert escrow_txn.amount == self.hold_amount
        assert escrow_txn.type == "debit"
        assert escrow_txn.reference == f"ORDER-{self.order_number}"
        assert escrow_txn.status == "completed"
        assert escrow_txn.metadata["escrow_status"] == "held"
        assert escrow_txn.metadata["is_escrow"] is True
        assert escrow_txn.metadata["can_refund"] is True

        # Assert db states
        self.assert_exists(
            Transaction,
            reference=f"ORDER-{self.order_number}",
            status="completed",
            metadata__escrow_status="held"
        )

    def test_hold_funds_insufficient_balance(self):
        """
        Verify that attempting to hold more funds than the wallet's balance
        raises a ValueError and does not modify the wallet balance.
        """
        initial_balance = self.wallet.balance
        excessive_amount = Decimal("20000.00")

        with pytest.raises(ValueError) as excinfo:
            EscrowManager.hold_funds(
                wallet=self.wallet,
                amount=excessive_amount,
                order_number=self.order_number
            )

        assert "Insufficient balance" in str(excinfo.value)
        assert self.wallet.balance == initial_balance

    def test_release_funds_success(self):
        """
        Verify that releasing held escrow funds updates the escrow status metadata
        to 'released' and disables further refunds without changing the wallet balance.
        """
        # Hold first
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )
        balance_after_hold = self.wallet.balance

        # Release funds
        updated_txn = EscrowManager.release_funds(order_number=self.order_number)

        # Assertions
        assert self.wallet.balance == balance_after_hold  # balance doesn't change on release
        assert updated_txn.metadata["escrow_status"] == "released"
        assert updated_txn.metadata["can_refund"] is False
        assert "released_at" in updated_txn.metadata

        # Verify database state
        self.assert_db_state(
            Transaction,
            updated_txn.pk,
            status="completed"
        )
        # Check through query
        txn = Transaction.objects.get(pk=updated_txn.pk)
        assert txn.metadata["escrow_status"] == "released"

    def test_release_funds_not_found(self):
        """
        Verify that trying to release escrow when no held transaction exists
        raises a ValueError.
        """
        with pytest.raises(ValueError) as excinfo:
            EscrowManager.release_funds(order_number="invalid-order")

        assert "No held escrow found" in str(excinfo.value)

    def test_refund_funds_full_success(self):
        """
        Verify that a full refund credits the wallet, marks the original escrow
        transaction as fully refunded, and creates a credit refund transaction.
        """
        # Hold first
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )
        balance_after_hold = self.wallet.balance

        # Perform full refund
        escrow_txn, refund_txn = EscrowManager.refund_funds(
            order_number=self.order_number,
            reason="Order canceled by merchant"
        )

        # Assertions
        assert self.wallet.balance == balance_after_hold + self.hold_amount
        assert escrow_txn.metadata["escrow_status"] == "refunded"
        assert escrow_txn.metadata["can_refund"] is False

        assert refund_txn.type == "credit"
        assert refund_txn.amount == self.hold_amount
        assert refund_txn.reference == f"REFUND-{self.order_number}"
        assert refund_txn.metadata["escrow_status"] == "refunded"
        assert refund_txn.metadata["refund_type"] == "full"

        # Verify db records
        self.assert_exists(
            Transaction,
            reference=f"REFUND-{self.order_number}",
            type="credit"
        )

    def test_refund_funds_partial_success(self):
        """
        Verify that a partial refund credits the wallet with the specified amount,
        keeps the original escrow transaction refundable (with remaining balance updated),
        and creates a partial credit refund transaction.
        """
        # Hold first
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )
        balance_after_hold = self.wallet.balance
        partial_amount = Decimal("1000.00")

        # Perform partial refund
        escrow_txn, refund_txn = EscrowManager.refund_funds(
            order_number=self.order_number,
            reason="Partial item cancellation",
            partial_amount=partial_amount
        )

        # Assertions
        assert self.wallet.balance == balance_after_hold + partial_amount
        assert escrow_txn.metadata["partial_refund"] == float(partial_amount)
        assert escrow_txn.metadata["remaining_escrow"] == float(self.hold_amount - partial_amount)
        # Note: Can still refund the remaining
        assert escrow_txn.metadata.get("can_refund", True) is True

        assert refund_txn.type == "credit"
        assert refund_txn.amount == partial_amount
        assert refund_txn.metadata["refund_type"] == "partial"

    def test_refund_funds_partial_excessive_amount(self):
        """
        Verify that requesting a partial refund greater than the escrowed amount
        raises a ValueError and does not modify database state.
        """
        # Hold first
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )
        excessive_refund = Decimal("5000.00")

        with pytest.raises(ValueError) as excinfo:
            EscrowManager.refund_funds(
                order_number=self.order_number,
                partial_amount=excessive_refund
            )

        assert "exceeds escrowed amount" in str(excinfo.value)

    def test_refund_funds_not_found(self):
        """
        Verify that attempting to refund an order with no refundable escrow
        raises a ValueError.
        """
        with pytest.raises(ValueError) as excinfo:
            EscrowManager.refund_funds(order_number="non-existent")

        assert "No refundable escrow found" in str(excinfo.value)

    def test_get_escrow_status_non_existent(self):
        """
        Verify that get_escrow_status returns exists=False for a non-existent order.
        """
        status_info = EscrowManager.get_escrow_status(order_number="9999999")
        assert status_info["exists"] is False
        assert status_info["escrow_status"] == "not_found"

    def test_get_escrow_status_held(self):
        """
        Verify that get_escrow_status returns complete information for a held escrow.
        """
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )

        status_info = EscrowManager.get_escrow_status(order_number=self.order_number)
        assert status_info["exists"] is True
        assert status_info["escrow_status"] == "held"
        assert status_info["amount"] == float(self.hold_amount)
        assert status_info["can_refund"] is True

    def test_get_total_escrowed_and_history(self):
        """
        Verify get_total_escrowed aggregates only currently held escrows,
        and get_escrow_history retrieves all escrow debits correctly.
        """
        # Make a second hold
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=self.hold_amount,
            order_number=self.order_number
        )
        EscrowManager.hold_funds(
            wallet=self.wallet,
            amount=Decimal("1500.00"),
            order_number="6158002"
        )

        # 1. Total Escrowed
        total_escrowed = EscrowManager.get_total_escrowed(self.wallet)
        assert total_escrowed == self.hold_amount + Decimal("1500.00")

        # 2. Escrow History
        history = EscrowManager.get_escrow_history(self.wallet)
        assert history.count() == 2

        # 3. Filtered History
        held_history = EscrowManager.get_escrow_history(self.wallet, status_filter="held")
        assert held_history.count() == 2

        # Release one
        EscrowManager.release_funds(order_number="6158002")

        # Total escrow should decrease
        assert EscrowManager.get_total_escrowed(self.wallet) == self.hold_amount

        # Completed history should now have 1 item
        completed = EscrowManager.get_completed_escrow_transactions(self.wallet)
        assert completed.count() == 1
        assert completed.first().reference == "ORDER-6158002"
