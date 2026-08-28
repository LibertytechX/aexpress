import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from dispatcher.models import Rider
from authentication.models import User
from orders.models import Order, Vehicle
from riders.models import RiderEarning, RiderCodRecord


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
class TestRiderEarnings:
    def test_earnings_today(self, api_client, rider_user, vehicle):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        # Create a completed order today
        order = Order.objects.create(
            user=user,  # Normally a merchant user, but for simplicity...
            rider=rider,
            vehicle=vehicle,
            pickup_address="A",
            total_amount=Decimal("1500.00"),
            status="Done",
            completed_at=timezone.now(),
        )

        # Create earning record
        RiderEarning.objects.create(
            rider=rider,
            order=order,
            net_earning=Decimal("1200.00"),
            created_at=timezone.now(),
        )

        # Create verified COD record
        RiderCodRecord.objects.create(
            rider=rider,
            order=order,
            amount=Decimal("1500.00"),
            status=RiderCodRecord.Status.VERIFIED,
            created_at=timezone.now(),
        )

        url = reverse("riders:rider-earnings")
        response = api_client.get(url, {"period": "today"})

        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert Decimal(data["total_earnings"]) == Decimal("1200.00")
        assert data["trips_completed"] == 1
        assert Decimal(data["cod_collected"]) == Decimal("1500.00")

    def test_earnings_filtering(self, api_client, rider_user, vehicle):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        # Create an order from yesterday
        yesterday = timezone.now() - timedelta(days=1)
        old_order = Order.objects.create(
            user=user,
            rider=rider,
            vehicle=vehicle,
            pickup_address="B",
            total_amount=Decimal("1000.00"),
            status="Done",
            completed_at=yesterday,
        )
        RiderEarning.objects.create(
            rider=rider,
            order=old_order,
            net_earning=Decimal("800.00"),
            created_at=yesterday,
        )

        url = reverse("riders:rider-earnings")

        # Today should be 0
        response = api_client.get(url, {"period": "today"})
        assert response.data["data"]["trips_completed"] == 0

        # Week should include it
        response = api_client.get(url, {"period": "week"})
        assert response.data["data"]["trips_completed"] == 1
