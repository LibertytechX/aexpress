import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from dispatcher.models import Rider
from authentication.models import User
from orders.models import Order, Vehicle
from riders.models import RiderCodRecord
from wallet.models import (
    Wallet,
    Bank,
    RiderPayoutTransaction,
    IndependentRiderPayoutWalletPool,
    IndependentRiderPayoutWalletPoolTransaction,
)
from wallet.integrations import WemaCoreBankingPayoutSDK


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def independent_rider_setup(db):
    pool = IndependentRiderPayoutWalletPool.get_default_pool()
    pool.balance = Decimal("1000000.00")
    pool.save(update_fields=["balance", "updated_at"])

    user = User.objects.create_user(
        phone="08022223333",
        password="password123",
        first_name="Indie",
        last_name="Rider",
    )
    rider = Rider.objects.create(
        user=user,
        rider_id="IND001",
        status="online",
        working_type="freelancer",
        is_independent_rider=True,
    )
    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet.balance = Decimal("10000.00")
    wallet.save()
    return user, rider, wallet


@pytest.fixture
def company_rider_setup(db):
    user = User.objects.create_user(
        phone="08033334444",
        password="password123",
        first_name="Company",
        last_name="Rider",
    )
    rider = Rider.objects.create(
        user=user,
        rider_id="CMP001",
        status="online",
        working_type="full_time",
        is_independent_rider=False,
    )
    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet.balance = Decimal("5000.00")
    wallet.save()
    return user, rider, wallet


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.get_or_create(
        name="Motorbike",
        defaults={
            "max_weight_kg": 15,
            "base_fare": 500.00,
            "rate_per_km": 100.00,
            "base_price": 500.00,
        },
    )[0]


@pytest.mark.django_db
class TestRiderBankListEndpoint:
    def test_bank_list_public_access(self, api_client):
        from django.core.management import call_command

        call_command("seed_banks")

        # Unauthenticated request should succeed
        url = reverse("riders:rider-banks")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        bank_names = [b["name"] for b in data["data"]]
        assert "Access Bank" in bank_names or "Wema Bank" in bank_names


@pytest.mark.django_db
class TestRiderVerifyAccountEndpoint:
    @patch("wallet.integrations.LibertyPayAccountEnquiryService.verify_account")
    def test_verify_account_success(self, mock_verify, api_client):
        mock_verify.return_value = {
            "account_number": "0123456789",
            "account_name": "JOHN DOE",
            "bank_code": "044",
            "currency_code": "NGN",
        }

        url = reverse("riders:rider-wallet-verify-account")
        payload = {"account_number": "0123456789", "bank_code": "044"}
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["data"]["account_name"] == "JOHN DOE"

    @patch("wallet.integrations.LibertyPayAccountEnquiryService.verify_account")
    def test_verify_account_failure(self, mock_verify, api_client):
        mock_verify.return_value = None

        url = reverse("riders:rider-wallet-verify-account")
        payload = {"account_number": "0000000000", "bank_code": "044"}
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Account verification failed" in str(response.data.get("message"))


@pytest.mark.django_db
class TestRiderWithdrawalEndpoint:
    def test_unauthenticated_blocked(self, api_client):
        url = reverse("riders:rider-wallet-withdraw")
        response = api_client.post(url, data={}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_company_rider_blocked(self, api_client, company_rider_setup):
        user, rider, wallet = company_rider_setup
        api_client.force_authenticate(user=user)

        url = reverse("riders:rider-wallet-withdraw")
        payload = {
            "amount": "1000.00",
            "account_number": "0123456789",
            "account_name": "Company Guy",
            "bank_code": "044",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only independent riders" in str(response.data.get("message"))

    def test_independent_rider_insufficient_wallet_balance(
        self, api_client, independent_rider_setup
    ):
        user, rider, wallet = independent_rider_setup
        api_client.force_authenticate(user=user)

        url = reverse("riders:rider-wallet-withdraw")
        payload = {
            "amount": "25000.00",  # Wallet only has 10,000
            "account_number": "0123456789",
            "account_name": "Indie Rider",
            "bank_code": "044",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient withdrawable balance" in str(response.data.get("message"))

    def test_independent_rider_cod_restriction(
        self, api_client, independent_rider_setup, vehicle
    ):
        user, rider, wallet = independent_rider_setup
        api_client.force_authenticate(user=user)

        # Wallet has 10,000. Add pending COD of 8,000.
        # Withdrawable balance = 10,000 - 8,000 = 2,000.
        order = Order.objects.create(
            user=user,
            rider=rider,
            vehicle=vehicle,
            pickup_address="Pickup A",
            total_amount=Decimal("8000.00"),
            status="Assigned",
        )
        RiderCodRecord.objects.create(
            rider=rider,
            order=order,
            amount=Decimal("8000.00"),
            status=RiderCodRecord.Status.PENDING,
        )

        url = reverse("riders:rider-wallet-withdraw")
        # Attempt to withdraw 3,000 (which is <= wallet balance 10,000 but > withdrawable 2,000)
        payload = {
            "amount": "3000.00",
            "account_number": "0123456789",
            "account_name": "Indie Rider",
            "bank_code": "044",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient withdrawable balance" in str(response.data.get("message"))
        assert "8,000.00" in str(response.data.get("message"))

    @patch.object(WemaCoreBankingPayoutSDK, "transfer_funds")
    def test_successful_withdrawal_flow(
        self, mock_transfer, api_client, independent_rider_setup
    ):
        user, rider, wallet = independent_rider_setup
        api_client.force_authenticate(user=user)

        mock_transfer.return_value = (
            True,
            {"status": "success", "reference": "WDR-MOCK-REF"},
        )

        url = reverse("riders:rider-wallet-withdraw")
        payload = {
            "amount": "3000.00",
            "account_number": "0123456789",
            "account_name": "Indie Rider",
            "bank_code": "044",
            "bank_name": "Access Bank",
            "narration": "Payout for trips",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert data["data"]["amount"] == 3000.0
        assert data["data"]["remaining_balance"] == 7000.0

        # Verify wallet debited
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("7000.00")

        # Verify pool debited
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        assert pool.balance == Decimal("997000.00")

        # Verify pool debit transaction created
        pool_txn = IndependentRiderPayoutWalletPoolTransaction.objects.filter(
            rider=rider, transaction_type="debit"
        ).first()
        assert pool_txn is not None
        assert pool_txn.amount == Decimal("3000.00")
        assert pool_txn.balance_before == Decimal("1000000.00")
        assert pool_txn.balance_after == Decimal("997000.00")
        assert pool_txn.status == "completed"

        # Verify RiderPayoutTransaction record created
        payout = RiderPayoutTransaction.objects.filter(rider=rider).first()
        assert payout is not None
        assert payout.amount == Decimal("3000.00")
        assert payout.status == RiderPayoutTransaction.Status.SUCCESS
        assert payout.destination_account_number == "0123456789"
        assert payout.pool == pool

        # Verify rider saved preferred bank details
        rider.refresh_from_db()
        assert rider.bank_account_number == "0123456789"
        assert rider.bank_name == "Access Bank"
        assert rider.bank_routing_code == "044"

    @patch.object(WemaCoreBankingPayoutSDK, "transfer_funds")
    def test_failed_transfer_triggers_automatic_refund(
        self, mock_transfer, api_client, independent_rider_setup
    ):
        user, rider, wallet = independent_rider_setup
        api_client.force_authenticate(user=user)

        # Mock CoreBanking failure
        mock_transfer.return_value = (
            False,
            {"status": "failed", "message": "Destination bank connection timeout"},
        )

        url = reverse("riders:rider-wallet-withdraw")
        payload = {
            "amount": "2000.00",
            "account_number": "0123456789",
            "account_name": "Indie Rider",
            "bank_code": "044",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "refunded" in str(response.data.get("message")).lower()

        # Wallet must be intact (10000 - 2000 + 2000 refund)
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("10000.00")

        # Payout pool must be refunded back to original balance (1000000 - 2000 + 2000 refund)
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        assert pool.balance == Decimal("1000000.00")

        # Verify refund credit transaction created on pool
        pool_refund_txn = IndependentRiderPayoutWalletPoolTransaction.objects.filter(
            rider=rider, transaction_type="credit"
        ).first()
        assert pool_refund_txn is not None
        assert pool_refund_txn.amount == Decimal("2000.00")
        assert pool_refund_txn.balance_before == Decimal("998000.00")
        assert pool_refund_txn.balance_after == Decimal("1000000.00")

        # Payout record marked as failed and refunded
        payout = RiderPayoutTransaction.objects.filter(rider=rider).first()
        assert payout is not None
        assert payout.status == RiderPayoutTransaction.Status.FAILED
        assert payout.refunded is True

    def test_insufficient_payout_pool_funds_blocks_withdrawal(
        self, api_client, independent_rider_setup
    ):
        user, rider, wallet = independent_rider_setup
        api_client.force_authenticate(user=user)

        # Set pool balance lower than withdrawal amount
        pool = IndependentRiderPayoutWalletPool.get_default_pool()
        pool.balance = Decimal("500.00")
        pool.save(update_fields=["balance", "updated_at"])

        url = reverse("riders:rider-wallet-withdraw")
        payload = {
            "amount": "2000.00",
            "account_number": "0123456789",
            "account_name": "Indie Rider",
            "bank_code": "044",
        }
        response = api_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient funds in payout pool" in str(response.data.get("message"))

        # Both wallet and pool balances must remain untouched
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("10000.00")
        pool.refresh_from_db()
        assert pool.balance == Decimal("500.00")

        # No payout record should have been created
        assert not RiderPayoutTransaction.objects.filter(rider=rider).exists()
        assert not IndependentRiderPayoutWalletPoolTransaction.objects.filter(rider=rider).exists()

