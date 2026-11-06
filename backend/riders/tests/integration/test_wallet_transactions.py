import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from dispatcher.models import Rider
from authentication.models import User
from wallet.models import Wallet, Transaction
from riders.models import RiderEarning
from orders.models import Order, Vehicle


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rider_user(db):
    user = User.objects.create_user(
        phone="08012345678",
        password="password123",
        first_name="Test",
        last_name="Rider",
    )
    rider = Rider.objects.create(user=user, rider_id="RID123", status="online")
    return user, rider


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        name="Bike",
        max_weight_kg=10,
        base_fare=500.00,
        rate_per_km=100.00,
        base_price=500.00,
    )


@pytest.mark.django_db
class TestRiderWalletTransactions:
    def test_transaction_list_empty(self, api_client, rider_user):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        url = reverse("riders:rider-wallet-transactions")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) == 0

    def test_transaction_list_with_data(self, api_client, rider_user):
        user, rider = rider_user
        api_client.force_authenticate(user=user)
        wallet, _ = Wallet.objects.get_or_create(user=user)

        # Create some transactions
        Transaction.objects.create(
            wallet=wallet,
            type="credit",
            amount=Decimal("1000.00"),
            description="Test Credit",
            balance_after=Decimal("1000.00"),
            status="completed",
        )
        Transaction.objects.create(
            wallet=wallet,
            type="debit",
            amount=Decimal("500.00"),
            description="Test Debit",
            balance_after=Decimal("500.00"),
            status="completed",
        )

        url = reverse("riders:rider-wallet-transactions")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2
        assert response.data["data"][0]["title"] == "Test Debit"
        assert response.data["data"][1]["title"] == "Test Credit"

    def test_earning_signal_credits_wallet(self, api_client, rider_user, vehicle):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        # Create an order
        order = Order.objects.create(
            user=user,
            rider=rider,
            vehicle=vehicle,
            pickup_address="A",
            total_amount=Decimal("2000.00"),
            status="Done",
        )

        # Create RiderEarning - this should trigger the signal
        earning = RiderEarning.objects.create(
            rider=rider, order=order, net_earning=Decimal("1600.00")
        )

        # Check wallet balance
        wallet = Wallet.objects.get(user=user)
        assert wallet.balance == Decimal("1600.00")

        # Check transaction record
        transaction = Transaction.objects.get(wallet=wallet, type="credit")
        assert transaction.amount == Decimal("1600.00")
        assert f"Trip earning: {order.order_number}" in transaction.description
        assert transaction.reference.startswith("EARN-")
