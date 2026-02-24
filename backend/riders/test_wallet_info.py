import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from dispatcher.models import Rider
from authentication.models import User
from orders.models import Order, Vehicle
from riders.models import RiderCodRecord
from wallet.models import Wallet


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rider_user(db):
    user = User.objects.create_user(
        phone="08011112222",
        password="password123",
        first_name="Wallet",
        last_name="Test",
    )
    rider = Rider.objects.create(user=user, rider_id="RID-WALLET", status="online")
    # Ensure wallet exists
    Wallet.objects.get_or_create(user=user, defaults={"balance": Decimal("5000.00")})
    return user, rider


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.get_or_create(
        name="Bike",
        defaults={
            "max_weight_kg": 10,
            "base_fare": 500.00,
            "rate_per_km": 100.00,
            "base_price": 500.00,
        },
    )[0]


@pytest.mark.django_db
class TestRiderWalletInfo:
    def test_wallet_info_basic(self, api_client, rider_user, vehicle):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        # 1. Check initial state (Balance: 5000, Pending COD: 0)
        url = reverse("riders:rider-wallet-info")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["available_balance"] == 5000.0
        assert data["pending_cod"] == 0.0

        # 2. Add some pending COD
        order = Order.objects.create(
            user=user,
            rider=rider,
            vehicle=vehicle,
            pickup_address="A",
            total_amount=Decimal("1500.00"),
            status="Assigned",
        )
        RiderCodRecord.objects.create(
            rider=rider,
            order=order,
            amount=Decimal("1500.00"),
            status=RiderCodRecord.Status.PENDING,
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        # Available Balance = 5000 (wallet) + 1500 (pending COD) = 6500
        assert data["available_balance"] == 6500.0
        assert data["pending_cod"] == 1500.0

        # 3. Mark COD as remitted (no longer pending)
        RiderCodRecord.objects.filter(order=order).update(
            status=RiderCodRecord.Status.REMITTED
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["available_balance"] == 5000.0
        assert data["pending_cod"] == 0.0
