import pytest
from decimal import Decimal
from django.contrib import admin
from authentication.models import User
from dispatcher.models import Rider
from wallet.models import (
    IndependentRiderPayoutWalletPool,
    IndependentRiderPayoutWalletPoolTransaction,
    PayoutWalletPool,
    PayoutWalletPoolTransaction,
    RiderPayoutTransaction,
)


@pytest.mark.django_db
class TestIndependentRiderPayoutWalletPool:
    def test_get_default_pool_creates_or_retrieves(self):
        pool1 = IndependentRiderPayoutWalletPool.get_default_pool()
        assert pool1 is not None
        assert pool1.name == "Independent Rider Payout Pool"
        assert pool1.is_active is True

        pool2 = IndependentRiderPayoutWalletPool.get_default_pool()
        assert pool1.id == pool2.id

    def test_pool_aliases(self):
        assert PayoutWalletPool is IndependentRiderPayoutWalletPool
        assert PayoutWalletPoolTransaction is IndependentRiderPayoutWalletPoolTransaction

    def test_has_sufficient_funds(self):
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        pool.balance = Decimal("5000.00")
        pool.save(update_fields=["balance", "updated_at"])

        assert pool.has_sufficient_funds(Decimal("3000.00")) is True
        assert pool.has_sufficient_funds(Decimal("5000.00")) is True
        assert pool.has_sufficient_funds(Decimal("5000.01")) is False

    def test_pool_credit_creates_ledger_entry(self):
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        pool.balance = Decimal("1000.00")
        pool.save(update_fields=["balance", "updated_at"])

        txn = pool.credit(
            amount=Decimal("500.00"),
            reference="TEST-CREDIT-001",
            description="Initial pool funding",
        )

        assert txn.transaction_type == "credit"
        assert txn.amount == Decimal("500.00")
        assert txn.balance_before == Decimal("1000.00")
        assert txn.balance_after == Decimal("1500.00")
        assert txn.status == "completed"

        pool.refresh_from_db()
        assert pool.balance == Decimal("1500.00")

    def test_pool_debit_creates_ledger_entry(self):
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        pool.balance = Decimal("2000.00")
        pool.save(update_fields=["balance", "updated_at"])

        user = User.objects.create_user(phone="08055551234", password="pw")
        rider = Rider.objects.create(user=user, rider_id="R90001", is_independent_rider=True)

        txn = pool.debit(
            amount=Decimal("750.00"),
            reference="TEST-DEBIT-001",
            rider=rider,
            description="Withdrawal debit",
        )

        assert txn.transaction_type == "debit"
        assert txn.amount == Decimal("750.00")
        assert txn.balance_before == Decimal("2000.00")
        assert txn.balance_after == Decimal("1250.00")
        assert txn.rider == rider
        assert txn.status == "completed"

        pool.refresh_from_db()
        assert pool.balance == Decimal("1250.00")

    def test_pool_debit_insufficient_funds_raises_value_error(self):
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        pool.balance = Decimal("300.00")
        pool.save(update_fields=["balance", "updated_at"])

        with pytest.raises(ValueError) as exc:
            pool.debit(amount=Decimal("1000.00"), reference="FAIL-REF")
        assert "Insufficient funds in payout pool" in str(exc.value)

        # Balance remains unchanged
        pool.refresh_from_db()
        assert pool.balance == Decimal("300.00")

    def test_models_registered_in_admin(self):
        assert IndependentRiderPayoutWalletPool in admin.site._registry
        assert IndependentRiderPayoutWalletPoolTransaction in admin.site._registry
        assert RiderPayoutTransaction in admin.site._registry
