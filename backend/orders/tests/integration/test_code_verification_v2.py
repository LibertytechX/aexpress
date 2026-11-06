from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import Rider, SystemSettings
from orders.models import Delivery, Order, Vehicle
from orders.serializers import AssignedOrderSerializer, OrderSerializer
from wallet.models import Wallet


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderCodeVerificationV2Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create primary rider
        self.rider_user = User.objects.create_user(
            phone="08011111111",
            email="rider1@test.com",
            password="password",
            usertype="Rider",
            contact_name="Test Rider",
        )
        self.rider_profile = self.rider_user.rider_profile
        self.client.force_authenticate(user=self.rider_user)

        # Create secondary rider (for unassigned tests)
        self.other_rider_user = User.objects.create_user(
            phone="08033333333",
            email="rider2@test.com",
            password="password",
            usertype="Rider",
            contact_name="Other Rider",
        )
        self.other_rider_profile = self.other_rider_user.rider_profile

        # Create merchant
        self.merchant = User.objects.create_user(
            phone="08022222222",
            email="merchant@test.com",
            password="password",
            usertype="Merchant",
            business_name="Acme Merchants",
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=500,
            rate_per_km=50,
            rate_per_minute=5,
            is_active=True,
        )

        # System settings for earnings calculation (20% commission)
        SystemSettings.objects.get_or_create(
            defaults={"commission_pct": Decimal("20.00")}
        )
        Wallet.objects.get_or_create(user=self.rider_user)

        # Create an assigned order
        self.order = Order.objects.create(
            user=self.merchant,
            rider=self.rider_profile,
            vehicle=self.vehicle,
            pickup_address="10 Marina, Lagos Island",
            pickup_latitude=6.45,
            pickup_longitude=3.40,
            total_amount=Decimal("1000.00"),
            status="Assigned",
        )

        # Create a single delivery for the order
        self.delivery = Delivery.objects.create(
            order=self.order,
            dropoff_address="5 Allen Avenue, Ikeja",
            dropoff_latitude=6.60,
            dropoff_longitude=3.35,
            receiver_name="Jane Doe",
            receiver_phone="08099999999",
            sequence=1,
        )

    def test_auto_code_generation(self):
        """Verify 6-digit numeric codes are generated automatically on Order and Delivery."""
        self.order.refresh_from_db()
        self.delivery.refresh_from_db()

        self.assertIsNotNone(self.order.pickup_code)
        self.assertEqual(len(self.order.pickup_code), 6)
        self.assertTrue(self.order.pickup_code.isdigit())

        self.assertIsNotNone(self.delivery.drop_code)
        self.assertEqual(len(self.delivery.drop_code), 6)
        self.assertTrue(self.delivery.drop_code.isdigit())

        # Test OrderSerializer (merchant facing) exposes pickup_code and drop_code
        serializer = OrderSerializer(self.order)
        self.assertEqual(serializer.data["pickup_code"], self.order.pickup_code)
        self.assertEqual(serializer.data["drop_code"], self.delivery.drop_code)

        # Test AssignedOrderSerializer (rider facing) hides pickup_code and drop_code
        rider_serializer = AssignedOrderSerializer(self.order)
        self.assertNotIn("pickup_code", rider_serializer.data)
        self.assertNotIn("drop_code", rider_serializer.data)

    def test_pickup_v2_success(self):
        """Rider confirms pickup with correct code regardless of GPS coordinates."""
        # Ensure rider has no GPS set or is arbitrarily far away
        self.rider_profile.current_latitude = 9.0765  # Abuja (far from Lagos)
        self.rider_profile.current_longitude = 7.3986
        self.rider_profile.save()

        url = reverse("orders:order_pickup_v2")
        payload = {
            "order_number": self.order.order_number,
            "pickup_code": self.order.pickup_code,
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PickedUp")
        self.assertIsNotNone(self.order.picked_up_at)
        self.assertIsNotNone(self.order.pickup_verified_at)
        self.assertEqual(self.order.pickup_code_attempts, 0)

    def test_pickup_v2_wrong_code_and_locking(self):
        """Rider gets 400 on wrong pickup code and locks after 5 consecutive failures."""
        url = reverse("orders:order_pickup_v2")

        # Wrong code 1
        payload = {
            "order_number": self.order.order_number,
            "pickup_code": "000000",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("4 attempt(s) remaining", response.data.get("message", ""))

        self.order.refresh_from_db()
        self.assertEqual(self.order.pickup_code_attempts, 1)

        # Fail 4 more times to reach 5
        for _ in range(4):
            self.client.post(url, payload, format="json")

        self.order.refresh_from_db()
        self.assertEqual(self.order.pickup_code_attempts, 5)

        # 6th attempt should return locked error even if correct code is entered
        valid_payload = {
            "order_number": self.order.order_number,
            "pickup_code": self.order.pickup_code,
        }
        locked_response = self.client.post(url, valid_payload, format="json")
        self.assertEqual(locked_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("locked", locked_response.data.get("message", "").lower())

    def test_pickup_v2_unassigned_rider_forbidden(self):
        """Other rider cannot pick up an order not assigned to them."""
        self.client.force_authenticate(user=self.other_rider_user)
        url = reverse("orders:order_pickup_v2")
        payload = {
            "order_number": self.order.order_number,
            "pickup_code": self.order.pickup_code,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_complete_v2_success(self):
        """Rider completes single-delivery order with drop code (via /v2/complete/)."""
        self.order.status = "PickedUp"
        self.order.save()

        url = reverse("orders:order_complete_v2")
        payload = {
            "order_number": self.order.order_number,
            "drop_code": self.delivery.drop_code,
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.order.refresh_from_db()
        self.delivery.refresh_from_db()

        self.assertEqual(self.delivery.status, "Delivered")
        self.assertEqual(self.order.status, "Done")
        self.assertIsNotNone(self.order.completed_at)
        self.assertIsNotNone(self.delivery.drop_verified_at)

        # Verify earnings were calculated and credited
        wallet = Wallet.objects.get(user=self.rider_user)
        # 20% of 1000 = 200
        self.assertEqual(wallet.balance, Decimal("200.00"))

    def test_delivery_deliver_v2_multi_drop(self):
        """In a multi-drop order, each leg is completed with its own drop code."""
        # Create second delivery
        delivery_2 = Delivery.objects.create(
            order=self.order,
            dropoff_address="12 Victoria Island, Lagos",
            receiver_name="Bob Smith",
            receiver_phone="08088888888",
            sequence=2,
        )

        self.order.status = "PickedUp"
        self.order.save()

        # Complete Leg 1 via /v2/delivery/<delivery_id>/deliver/
        url_1 = reverse("orders:delivery_deliver_v2", kwargs={"delivery_id": str(self.delivery.id)})
        res_1 = self.client.post(url_1, {"drop_code": self.delivery.drop_code}, format="json")
        self.assertEqual(res_1.status_code, status.HTTP_200_OK)

        self.delivery.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.delivery.status, "Delivered")
        self.assertNotEqual(self.order.status, "Done")  # Order should NOT be done yet

        # Complete Leg 2
        url_2 = reverse("orders:delivery_deliver_v2", kwargs={"delivery_id": str(delivery_2.id)})
        res_2 = self.client.post(url_2, {"drop_code": delivery_2.drop_code}, format="json")
        self.assertEqual(res_2.status_code, status.HTTP_200_OK)

        delivery_2.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(delivery_2.status, "Delivered")
        self.assertEqual(self.order.status, "Done")  # Now order is Done

        # Verify earnings credited once
        wallet = Wallet.objects.get(user=self.rider_user)
        self.assertEqual(wallet.balance, Decimal("200.00"))

    def test_delivery_v2_wrong_code_and_locking(self):
        """Delivery completion enforces max 5 failed attempts on drop code."""
        url = reverse("orders:delivery_deliver_v2", kwargs={"delivery_id": str(self.delivery.id)})

        # 5 failed attempts
        for _ in range(5):
            res = self.client.post(url, {"drop_code": "000000"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.drop_code_attempts, 5)

        # 6th attempt locked
        res_locked = self.client.post(url, {"drop_code": self.delivery.drop_code}, format="json")
        self.assertEqual(res_locked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("locked", res_locked.data.get("message", "").lower())

