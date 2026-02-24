from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from authentication.models import User
from orders.models import Order, Delivery, Vehicle
from dispatcher.models import Rider


class RiderOrderEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a rider user
        self.rider_user = User.objects.create_user(
            phone="08012345678",
            email="rider@example.com",
            password="password123",
            usertype="Rider",
            contact_name="Rider One",
        )
        self.rider_profile = Rider.objects.create(user=self.rider_user)
        self.client.force_authenticate(user=self.rider_user)

        # Create a merchant user
        self.merchant = User.objects.create_user(
            phone="08087654321",
            email="merchant@example.com",
            password="password123",
            usertype="Merchant",
            contact_name="Merchant One",
            business_name="Merchant Biz",
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )

        # Create an order
        self.order = Order.objects.create(
            user=self.merchant,
            rider=self.rider_profile,
            vehicle=self.vehicle,
            pickup_address="123 Pickup St",
            sender_name="Sender",
            sender_phone="08011111111",
            total_amount=1000,
            status="Assigned",
        )
        # Create a delivery
        self.delivery = Delivery.objects.create(
            order=self.order,
            dropoff_address="456 Dropoff Ave",
            receiver_name="Receiver",
            receiver_phone="08022222222",
            sequence=1,
            status="Pending",
        )

    def test_order_start_endpoint(self):
        url = reverse("orders:order_start")
        data = {
            "order_number": self.order.order_number,
            "latitude": 6.45,
            "longitude": 3.39,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Started")

        # Verify event logged
        self.assertTrue(self.order.events.filter(event="Order Started").exists())

    def test_order_arrived_endpoint(self):
        self.order.status = "Started"
        self.order.save()

        url = reverse("orders:order_arrived")
        data = {
            "order_number": self.order.order_number,
            "latitude": 6.45,
            "longitude": 3.39,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Arrived")
        self.assertIsNotNone(self.order.arrived_at)

        # Verify event logged
        self.assertTrue(
            self.order.events.filter(event="Rider Arrived at Pickup").exists()
        )

    def test_order_complete_endpoint(self):
        self.order.status = "PickedUp"
        self.order.save()

        url = reverse("orders:order_complete")
        data = {
            "order_number": self.order.order_number,
            "latitude": 6.45,
            "longitude": 3.39,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Done")
        self.assertIsNotNone(self.order.completed_at)

        # Verify delivery is also marked as Delivered
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, "Delivered")
        self.assertIsNotNone(self.delivery.delivered_at)

        # Verify event logged
        self.assertTrue(
            self.order.events.filter(event="Order Completed (All Deliveries)").exists()
        )
