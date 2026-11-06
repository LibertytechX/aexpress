from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
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

        # Create SystemSettings and Wallet for completion tests
        from dispatcher.models import SystemSettings
        from wallet.models import Wallet

        SystemSettings.objects.get_or_create(
            defaults={"commission_pct": 20}
        )
        Wallet.objects.get_or_create(user=self.rider_user)

    @patch("orders.views.calculate_route")
    def test_pickup_allowed_within_range(self, mock_calc):
        """Test pickup is allowed when within 2km via route."""
        mock_calc.return_value = {"distance_km": 0.5, "duration_mins": 2.5}
        url = reverse("orders:order_pickup")
        # Set coordinates on rider profile since the view uses profile coordinates
        self.rider_profile.current_latitude = 6.4501
        self.rider_profile.current_longitude = 3.4001
        self.rider_profile.save()
        data = {
            "order_number": self.order.order_number,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PickedUp")
        mock_calc.assert_called_once()

    @patch("orders.views.calculate_route")
    def test_pickup_denied_out_of_range(self, mock_calc):
        """Test pickup is denied when too far via route (> 2km)."""
        mock_calc.return_value = {"distance_km": 3.2, "duration_mins": 10.0}
        url = reverse("orders:order_pickup")
        # Set coordinates on rider profile since the view uses profile coordinates
        self.rider_profile.current_latitude = 6.47
        self.rider_profile.current_longitude = 3.40
        self.rider_profile.save()
        data = {
            "order_number": self.order.order_number,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data.get("error", response.data.get("message", ""))
        self.assertIn("too far", error_msg)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Assigned")
        mock_calc.assert_called_once()

    @patch("orders.views.calculate_route")
    def test_pickup_allowed_fallback(self, mock_calc):
        """Test pickup is allowed via haversine fallback when routing API fails."""
        mock_calc.return_value = None  # Force fallback
        url = reverse("orders:order_pickup")
        self.rider_profile.current_latitude = 6.4501
        self.rider_profile.current_longitude = 3.4001
        self.rider_profile.save()
        data = {
            "order_number": self.order.order_number,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PickedUp")

    def test_pickup_denied_missing_coordinates(self):
        """Test coordinates are required for pickup."""
        url = reverse("orders:order_pickup")
        self.rider_profile.current_latitude = None
        self.rider_profile.current_longitude = None
        self.rider_profile.save()
        data = {"order_number": self.order.order_number}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data.get("error", response.data.get("message", ""))
        self.assertIn("Latitude and longitude are required", error_msg)

    @patch("orders.views.calculate_route")
    def test_status_change_pickup_proximity(self, mock_calc):
        """Test OrderStatusChangeView also enforces proximity for 'pickup' action."""
        mock_calc.return_value = {"distance_km": 4.5, "duration_mins": 12.0}
        url = reverse("orders:order_status_change")
        # Too far
        self.rider_profile.current_latitude = 6.47
        self.rider_profile.current_longitude = 3.40
        self.rider_profile.save()
        data = {
            "order_number": self.order.order_number,
            "action": "pickup",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data.get("error", response.data.get("message", ""))
        self.assertIn("too far", error_msg)

    def test_delivery_complete_proximity(self):
        """Test DeliveryCompleteView proximity enforcement."""
        from orders.models import Delivery

        deliv = Delivery.objects.create(
            order=self.order,
            dropoff_address="Dropoff",
            dropoff_latitude=6.45,
            dropoff_longitude=3.50,
            receiver_name="Recv",
            receiver_phone="080",
        )
        url = reverse("orders:delivery_deliver", kwargs={"delivery_id": deliv.id})

        # Too far (3.40 vs 3.50 is many km)
        data = {"latitude": 6.45, "longitude": 3.40}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data.get("error", response.data.get("message", ""))
        self.assertIn("too far", error_msg)

        # Close enough
        data = {"latitude": 6.4501, "longitude": 3.5001}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("orders.views.calculate_route")
    def test_order_complete_proximity(self, mock_calc):
        """Test OrderCompleteView proximity enforcement via route."""
        from orders.models import Delivery

        # Update existing order to have a dropoff location
        self.order.status = "PickedUp"
        self.order.save()

        Delivery.objects.create(
            order=self.order,
            dropoff_address="Final Dropoff",
            dropoff_latitude=6.50,
            dropoff_longitude=3.50,
            receiver_name="Recv",
            receiver_phone="080",
            sequence=2,
        )

        url = reverse(
            "order_complete", kwargs={"order_number": self.order.order_number}
        )

        # 1. Too far
        mock_calc.return_value = {"distance_km": 5.2, "duration_mins": 15.0}
        self.rider_profile.current_latitude = 6.45
        self.rider_profile.current_longitude = 3.40
        self.rider_profile.save()
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data.get("error", response.data.get("message", ""))
        self.assertIn("too far", error_msg)

        # 2. Close enough
        mock_calc.return_value = {"distance_km": 0.2, "duration_mins": 1.5}
        self.rider_profile.current_latitude = 6.5001
        self.rider_profile.current_longitude = 3.5001
        self.rider_profile.save()
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    @patch("orders.views.calculate_route")
    def test_order_complete_proximity_fallback(self, mock_calc):
        """Test OrderCompleteView proximity enforcement fallback when routing fails."""
        from orders.models import Delivery

        # Force routing API to return None (triggering fallback)
        mock_calc.return_value = None

        # Reset order status
        self.order.status = "PickedUp"
        self.order.save()

        # Re-fetch or reuse order number with sequence=2 delivery
        Delivery.objects.create(
            order=self.order,
            dropoff_address="Final Dropoff",
            dropoff_latitude=6.50,
            dropoff_longitude=3.50,
            receiver_name="Recv2",
            receiver_phone="081",
            sequence=3,
        )

        url = reverse(
            "order_complete", kwargs={"order_number": self.order.order_number}
        )

        # 1. Too far via fallback (haversine)
        self.rider_profile.current_latitude = 6.45
        self.rider_profile.current_longitude = 3.40
        self.rider_profile.save()
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Close enough via fallback (haversine)
        self.rider_profile.current_latitude = 6.5001
        self.rider_profile.current_longitude = 3.5001
        self.rider_profile.save()
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
