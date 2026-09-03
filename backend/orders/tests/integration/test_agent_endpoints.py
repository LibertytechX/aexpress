"""
Integration tests for Assured Express (AXpress) AI Agent Endpoints.
Tests:
- Quote calculation (POST /api/orders/quote/)
- Agent order booking (POST /api/orders/agent/book/)
- Order tracking (GET /api/orders/track/<order_id>/)
- Customer deliveries history (GET /api/orders/customer-deliveries/)
- Order payment info (GET /api/orders/<order_id>/payment-info/)
"""

from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import User
from orders.models import Delivery, Order, OrderEvent, Vehicle
from wallet.models import VirtualAccount, Wallet


class AgentEndpointsTests(APITestCase):
    """Test suite for AI Agent / MCP endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create(
            phone="2348011112222",
            contact_name="Test Merchant",
            email="merchant@test.com",
            usertype="Merchant",
        )
        self.wallet = getattr(self.user, "wallet", None)
        if not self.wallet:
            self.wallet = Wallet.objects.filter(user=self.user).first()
        if not self.wallet:
            self.wallet = Wallet.objects.create(user=self.user)
        self.wallet.balance = Decimal("10000.00")
        self.wallet.save()

        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=25,
            base_price=Decimal("500.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("150.00"),
            rate_per_minute=Decimal("10.00"),
            min_fee=Decimal("800.00"),
            is_active=True,
        )

        self.car = Vehicle.objects.create(
            name="Car",
            max_weight_kg=100,
            base_price=Decimal("1200.00"),
            base_fare=Decimal("1200.00"),
            rate_per_km=Decimal("250.00"),
            rate_per_minute=Decimal("20.00"),
            min_fee=Decimal("1800.00"),
            is_active=True,
        )

    @patch("orders.agent_views.calculate_route")
    @patch("orders.agent_views.geocode_address")
    def test_quote_endpoint_defaults_to_bike(self, mock_geocode, mock_route):
        """Test quote endpoint calculates route and defaults vehicle to Bike."""
        mock_geocode.side_effect = [
            {"lat": 6.45, "lng": 3.42},
            {"lat": 6.60, "lng": 3.35},
        ]
        mock_route.return_value = {"distance_km": 15.0, "duration_minutes": 30}

        url = reverse("orders:order_quote")
        payload = {
            "pickup_location": "Admiralty Way, Lekki",
            "delivery_location": "Ikeja City Mall, Alausa",
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]

        self.assertEqual(data["selected_vehicle"], "Bike")
        self.assertEqual(data["distance_km"], 15.0)
        self.assertEqual(data["duration_minutes"], 30)
        self.assertIn("₦", data["formatted_price"])
        self.assertTrue(len(data["quotes"]) >= 2)

    @patch("orders.agent_views.calculate_route")
    @patch("orders.agent_views.geocode_address")
    def test_agent_book_order_success(self, mock_geocode, mock_route):
        """Test agent book order creates Order and Delivery without manual distance."""
        mock_geocode.side_effect = [
            {"lat": 6.45, "lng": 3.42},
            {"lat": 6.60, "lng": 3.35},
        ]
        mock_route.return_value = {"distance_km": 10.0, "duration_minutes": 20}

        url = reverse("orders:agent_book_order")
        payload = {
            "pickup_address": "12 Admiralty Way, Lekki Phase 1",
            "sender_name": "Test Merchant",
            "sender_phone": "2348011112222",
            "dropoff_address": "Plot 5, Victoria Island",
            "receiver_name": "John Doe",
            "receiver_phone": "2348099998888",
            "vehicle": "Bike",
            "notes": "Handle with care",
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]

        self.assertIn("order_number", data)
        self.assertEqual(data["pickup_address"], "12 Admiralty Way, Lekki Phase 1")
        self.assertEqual(data["dropoff_address"], "Plot 5, Victoria Island")

        # Verify DB records
        order = Order.objects.get(order_number=data["order_number"])
        self.assertEqual(order.sender_name, "Test Merchant")
        self.assertEqual(order.deliveries.count(), 1)
        delivery = order.deliveries.first()
        self.assertEqual(delivery.receiver_name, "John Doe")

    def test_order_tracking_endpoint(self):
        """Test order tracking returns order status and timeline."""
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            order_number="6999001",
            pickup_address="10 Marina, Lagos Island",
            sender_name="Sender One",
            sender_phone="2348011112222",
            total_amount=Decimal("1500.00"),
            status="Pending",
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="20 Broad Street, Lagos",
            receiver_name="Receiver One",
            receiver_phone="2348033334444",
        )
        OrderEvent.objects.create(
            order=order,
            event="created",
            description="Order created via AI Agent",
        )

        url = reverse("orders:order_track", kwargs={"order_id": order.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]

        self.assertEqual(data["order_number"], "6999001")
        self.assertEqual(data["status"], "Pending")
        self.assertEqual(data["pickup_address"], "10 Marina, Lagos Island")
        self.assertTrue(len(data["timeline"]) >= 1)

    def test_customer_deliveries_endpoint(self):
        """Test customer deliveries lookup by sender and receiver phone."""
        order1 = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            order_number="6999002",
            pickup_address="Origin A",
            sender_name="Sender Phone Test",
            sender_phone="+2348055556666",
            total_amount=Decimal("2000.00"),
            status="InTransit",
        )
        Delivery.objects.create(
            order=order1,
            dropoff_address="Destination A",
            receiver_name="Receiver A",
            receiver_phone="+2348077778888",
        )

        url = reverse("orders:customer_deliveries")
        # Query as sender
        response = self.client.get(url, {"phone": "08055556666"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["deliveries"][0]["role"], "Sender")

        # Query as receiver
        response2 = self.client.get(url, {"phone": "+2348077778888"})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.data["data"]
        self.assertEqual(data2["count"], 1)
        self.assertEqual(data2["deliveries"][0]["role"], "Receiver")

    @patch("orders.agent_views.create_virtual_account")
    def test_order_payment_info_endpoint(self, mock_create_va):
        """Test retrieving payment info and virtual account for an order."""
        va = VirtualAccount.objects.create(
            user=self.user,
            account_number="9988776655",
            account_name="Test Merchant AXPRESS",
            bank_name="Wema Bank",
            bank_code="035",
        )
        mock_create_va.return_value = va

        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            order_number="6999003",
            pickup_address="Lekki",
            sender_name="Test Merchant",
            sender_phone="2348011112222",
            total_amount=Decimal("3500.00"),
            payment_status="Pending",
        )

        url = reverse("orders:order_payment_info", kwargs={"order_id": order.order_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]

        self.assertEqual(data["order_number"], "6999003")
        self.assertEqual(data["total_amount"], 3500.0)
        self.assertEqual(data["virtual_account"]["account_number"], "9988776655")
        self.assertIn("9988776655", data["instructions"])
