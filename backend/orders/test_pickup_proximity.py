from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User
from orders.models import Order, Vehicle
from dispatcher.models import Rider


class PickupProximityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.rider_user = User.objects.create_user(
            phone="08011111111",
            email="rider@test.com",
            password="password",
            usertype="Rider",
            contact_name="Test Rider",
        )
        self.rider_profile = self.rider_user.rider_profile
        self.client.force_authenticate(user=self.rider_user)

        self.merchant = User.objects.create_user(
            phone="08022222222",
            email="merchant@test.com",
            password="password",
            usertype="Merchant",
        )

        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=500,
            rate_per_km=50,
            rate_per_minute=5,
            is_active=True,
        )

        # Lagos Island area: ~6.45, 3.40
        self.order = Order.objects.create(
            user=self.merchant,
            rider=self.rider_profile,
            vehicle=self.vehicle,
            pickup_address="Lagos Island",
            pickup_latitude=6.45,
            pickup_longitude=3.40,
            total_amount=1000,
            status="Assigned",
        )

    def test_pickup_allowed_within_range(self):
        """Test pickup is allowed when within 500m (e.g. 100m away)."""
        url = reverse("orders:order_pickup")
        # 6.4501 is roughly 11m north of 6.45
        data = {
            "order_number": self.order.order_number,
            "latitude": 6.4501,
            "longitude": 3.4001,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PickedUp")

    def test_pickup_denied_out_of_range(self):
        """Test pickup is denied when too far (e.g. 1km away)."""
        url = reverse("orders:order_pickup")
        # 6.46 is roughly 1.1km north of 6.45
        data = {
            "order_number": self.order.order_number,
            "latitude": 6.46,
            "longitude": 3.40,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too far", response.data["error"])
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Assigned")

    def test_pickup_denied_missing_coordinates(self):
        """Test coordinates are required for pickup."""
        url = reverse("orders:order_pickup")
        data = {"order_number": self.order.order_number}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Latitude and longitude are required", response.data["error"])

    def test_status_change_pickup_proximity(self):
        """Test OrderStatusChangeView also enforces proximity for 'pickup' action."""
        url = reverse("orders:order_status_change")
        # Too far
        data = {
            "order_number": self.order.order_number,
            "action": "pickup",
            "latitude": 6.47,
            "longitude": 3.40,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too far", response.data["error"])
