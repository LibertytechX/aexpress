from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import User
from orders.models import Order, Delivery, Vehicle, OrderEvent
from dispatcher.models import Rider
from django.utils import timezone
from decimal import Decimal


class DeliveryEndpointsTests(APITestCase):
    def setUp(self):
        # Create merchant user
        self.merchant = User.objects.create_user(
            phone="08011112222",
            email="merchant@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Test Business",
            contact_name="Test Merchant",
        )

        # Create rider user and profile
        self.rider_user = User.objects.create_user(
            phone="08033334444",
            email="rider@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Test Rider",
        )
        self.rider_profile = Rider.objects.create(
            user=self.rider_user, is_authorized=True, is_active=True
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            name="Test Bike",
            max_weight_kg=100,
            base_price=Decimal("500.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("100.00"),
            rate_per_minute=Decimal("20.00"),
            min_fee=Decimal("500.00"),
        )

        # Create order
        self.order = Order.objects.create(
            user=self.merchant,
            rider=self.rider_profile,
            vehicle=self.vehicle,
            pickup_address="123 Pickup St",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            status="PickedUp",
        )

        # Create deliveries
        self.delivery1 = Delivery.objects.create(
            order=self.order,
            dropoff_address="456 Dropoff Rd",
            receiver_name="Receiver 1",
            receiver_phone="08055556666",
            sequence=1,
            status="Pending",
        )
        self.delivery2 = Delivery.objects.create(
            order=self.order,
            dropoff_address="789 Dropoff Ave",
            receiver_name="Receiver 2",
            receiver_phone="08077778888",
            sequence=2,
            status="Pending",
        )

    def test_delivery_start(self):
        """Test marking a delivery as InTransit."""
        self.client.force_authenticate(user=self.rider_user)
        url = reverse(
            "orders:delivery_start", kwargs={"delivery_id": str(self.delivery1.id)}
        )
        data = {"latitude": 6.45, "longitude": 3.39}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "InTransit")

        # Check delivery status
        self.delivery1.refresh_from_db()
        self.assertEqual(self.delivery1.status, "InTransit")

        # Check order status (should be Started since order was PickedUp)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Started")

        # Check rider location
        self.rider_profile.refresh_from_db()
        self.assertAlmostEqual(
            float(self.rider_profile.current_latitude), 6.45, places=2
        )
        self.assertAlmostEqual(
            float(self.rider_profile.current_longitude), 3.39, places=2
        )

    def test_delivery_complete_partial(self):
        """Test completing one delivery in a multi-drop order."""
        self.client.force_authenticate(user=self.rider_user)

        # Start delivery 1 first
        self.delivery1.status = "InTransit"
        self.delivery1.save()
        self.order.status = "Started"
        self.order.save()

        url = reverse(
            "orders:delivery_deliver", kwargs={"delivery_id": str(self.delivery1.id)}
        )
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.delivery1.refresh_from_db()
        self.assertEqual(self.delivery1.status, "Delivered")
        self.assertIsNotNone(self.delivery1.delivered_at)

        # Order should still be Started because delivery2 is Pending
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Started")

    def test_delivery_complete_all(self):
        """Test completing all deliveries in an order."""
        self.client.force_authenticate(user=self.rider_user)

        # Set both deliveries to InTransit
        self.delivery1.status = "InTransit"
        self.delivery1.save()
        self.delivery2.status = "InTransit"
        self.delivery2.save()
        self.order.status = "Started"
        self.order.save()

        # Deliver first
        url1 = reverse(
            "orders:delivery_deliver", kwargs={"delivery_id": str(self.delivery1.id)}
        )
        self.client.post(url1, {}, format="json")

        # Deliver second
        url2 = reverse(
            "orders:delivery_deliver", kwargs={"delivery_id": str(self.delivery2.id)}
        )
        response = self.client.post(url2, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Order should now be Done
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Done")
