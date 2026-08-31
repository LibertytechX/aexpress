from typing import Any
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal
from authentication.models import User
from orders.models import Vehicle, Order
from wallet.models import Wallet


class QuickSendSmartParcelTests(APITestCase):
    """Test suite for Quick Send order creation with SmartParcel locker details."""

    def setUp(self) -> None:
        """Set up test data and authentication."""
        self.merchant: User = User.objects.create_user(
            phone="08011112222",
            email="merchant@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Test Business",
            contact_name="Test Merchant",
        )
        self.client.force_authenticate(user=self.merchant)

        # Ensure merchant has a wallet with enough balance
        self.wallet, _ = Wallet.objects.get_or_create(user=self.merchant)
        self.wallet.balance = Decimal("10000.00")
        self.wallet.save()

        self.vehicle: Vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=100,
            base_price=Decimal("500.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("100.00"),
            rate_per_minute=Decimal("20.00"),
            min_fee=Decimal("500.00"),
            is_active=True,
        )

        self.url: str = reverse("orders:quick_send")

    @patch("orders.views.get_order_service")
    def test_quick_send_smart_parcel_delivery_success(
        self, mock_get_order_service: MagicMock
    ) -> None:
        """Verify successful order creation when delivering to a SmartParcel locker.

        This test checks that the sender's phone number is correctly retrieved
        and passed to the parcel payload without any typos.
        """
        # Mock order service and its process_parcel_delivery method
        mock_service: MagicMock = MagicMock()
        mock_get_order_service.return_value = mock_service

        mock_service.process_parcel_delivery.return_value = (
            True,
            {
                "status_code": 200,
                "pickup_address": "123 Pickup St",
                "dropoff_address": "SmartParcel Locker Address",
                "parcel_info": {"trackingnumber": "SP1234567"},
            },
        )
        mock_service.process_non_cash_payment.return_value = (True, {})

        payload: dict[str, Any] = {
            "pickup_address": "123 Pickup St",
            "sender_name": "Test Sender",
            "sender_phone": "08011112222",
            "dropoff_address": "Original Dropoff Address",
            "receiver_name": "Test Receiver",
            "receiver_phone": "08033334444",
            "vehicle": "Bike",
            "payment_method": "wallet",
            "package_type": "Box",
            "notes": "Locker delivery",
            "distance_km": "5.5",
            "duration_minutes": 15,
            "isdelivery_percel": True,
            "box_id": "BOX_99",
            "locker_size_id": "SIZE_M",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert process_parcel_delivery was called with correct arguments
        mock_service.process_parcel_delivery.assert_called_once()
        args, kwargs = mock_service.process_parcel_delivery.call_args
        
        # args[0] is is_pickup_percel (False), args[1] is isdelivery_percel (True)
        self.assertFalse(args[0])
        self.assertTrue(args[1])
        
        # args[3] is the parcel_payload dict
        parcel_payload = args[3]
        self.assertEqual(parcel_payload["sendername"], "Test Sender")
        # Ensure that 'senderphone' maps to data.get('sender_phone') (and not empty due to space typo)
        self.assertEqual(parcel_payload["senderphone"], "08011112222")
        self.assertEqual(parcel_payload["recipientname"], "Test Receiver")
        self.assertEqual(parcel_payload["recipientphone"], "08033334444")
        self.assertEqual(parcel_payload["boxid"], "BOX_99")
        self.assertEqual(parcel_payload["sizeid"], "SIZE_M")
