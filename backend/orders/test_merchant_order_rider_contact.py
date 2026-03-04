from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import User
from dispatcher.models import Rider
from orders.models import Delivery, Order, Vehicle


class MerchantOrderRiderContactTests(APITestCase):
    def setUp(self):
        self.merchant = User.objects.create_user(
            phone="08011112222",
            email="merchant_rider_contact@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Test Business",
            contact_name="Test Merchant",
        )

        self.rider_user = User.objects.create_user(
            phone="08033334444",
            email="rider_rider_contact@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Test Rider",
        )
        self.rider_profile = Rider.objects.create(user=self.rider_user, rider_id="168817")

        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=100,
            base_price=Decimal("500.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("100.00"),
            rate_per_minute=Decimal("20.00"),
            min_fee=Decimal("500.00"),
        )

        self.order = Order.objects.create(
            order_number="6158001",
            user=self.merchant,
            rider=self.rider_profile,
            vehicle=self.vehicle,
            pickup_address="123 Pickup St",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            status="Assigned",
        )
        Delivery.objects.create(
            order=self.order,
            dropoff_address="456 Dropoff Rd",
            receiver_name="Receiver",
            receiver_phone="08055556666",
            sequence=1,
            status="Pending",
        )

    def test_order_list_includes_rider_contact_fields(self):
        self.client.force_authenticate(user=self.merchant)
        url = reverse("orders:order_list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get("success"))
        orders = res.data.get("orders")
        self.assertTrue(isinstance(orders, list) and len(orders) >= 1)

        first = orders[0]
        self.assertEqual(first.get("rider_code"), "168817")
        self.assertEqual(first.get("rider_name"), "Test Rider")
        self.assertEqual(first.get("rider_phone"), "08033334444")

    def test_order_detail_includes_rider_contact_fields(self):
        self.client.force_authenticate(user=self.merchant)
        url = reverse("orders:order_detail", kwargs={"order_number": self.order.order_number})
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get("success"))
        order = res.data.get("order")

        self.assertEqual(order.get("rider_code"), "168817")
        self.assertEqual(order.get("rider_name"), "Test Rider")
        self.assertEqual(order.get("rider_phone"), "08033334444")

    def test_order_detail_scoped_to_authenticated_user(self):
        other = User.objects.create_user(
            phone="08099990000",
            email="other_merchant@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Other Business",
            contact_name="Other Merchant",
        )
        self.client.force_authenticate(user=other)
        url = reverse("orders:order_detail", kwargs={"order_number": self.order.order_number})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
