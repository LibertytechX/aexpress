import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User
from dispatcher.models import Rider
from orders.models import Order, Delivery, Vehicle
from riders.models import RiderEarning


@pytest.mark.django_db
class TestTodayTrips:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone="08012345678",
            password="password123",
            first_name="Test",
            last_name="Merchant",
            business_name="Test Business",
        )
        self.rider_user = User.objects.create_user(
            phone="08087654321",
            password="password123",
            first_name="Test",
            last_name="Rider",
        )
        self.rider = Rider.objects.create(
            user=self.rider_user, rider_id="R-123", status="online"
        )
        self.vehicle = Vehicle.objects.create(
            name="Motorcycle",
            max_weight_kg=20,
            base_price=500,
            base_fare=500,
            rate_per_km=100,
            rate_per_minute=10,
            min_distance_km=2,
            min_fee=1000,
        )
        self.client.force_authenticate(user=self.rider_user)

    def test_today_trips_endpoint(self):
        now = timezone.now()

        # 1. Completed today
        order1 = Order.objects.create(
            order_number="ORDER001",
            user=self.user,
            rider=self.rider,
            vehicle=self.vehicle,
            status="Done",
            completed_at=now - timedelta(hours=2),
            pickup_address="Surulere, Lagos",
            total_amount=2800,
            distance_km=12.4,
        )
        Delivery.objects.create(
            order=order1, dropoff_address="V.I., Lagos", cod_amount=8037
        )
        RiderEarning.objects.create(rider=self.rider, order=order1, net_earning=2500)

        # 2. Completed today
        order2 = Order.objects.create(
            order_number="ORDER002",
            user=self.user,
            rider=self.rider,
            vehicle=self.vehicle,
            status="Done",
            completed_at=now - timedelta(hours=4),
            pickup_address="Ikeja, Lagos",
            total_amount=1500,
            distance_km=8.1,
        )
        Delivery.objects.create(
            order=order2, dropoff_address="Yaba, Lagos", cod_amount=0
        )
        RiderEarning.objects.create(rider=self.rider, order=order2, net_earning=1200)

        # 3. Completed yesterday
        yesterday = now - timedelta(days=1)
        order3 = Order.objects.create(
            order_number="ORDER003",
            user=self.user,
            rider=self.rider,
            vehicle=self.vehicle,
            status="Done",
            completed_at=yesterday,
            pickup_address="Lekki, Lagos",
            total_amount=2100,
            distance_km=6.3,
        )
        Delivery.objects.create(
            order=order3, dropoff_address="Ajah, Lagos", cod_amount=15000
        )

        url = "/api/riders/orders/today/"
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]

        # Should only contain 2 orders from today
        assert len(data) == 2

        # Check first order fields
        first_order = data[0]
        assert first_order["id"] == "ORDER001"
        assert "Surulere -> V.I." in first_order["route"]
        assert "12.4km" in first_order["distance"]
        assert first_order["earned"] == 2500.0
        assert first_order["cod"] == 8037.0
        assert first_order["time"] is not None
