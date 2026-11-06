from typing import Any
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal

from authentication.models import User
from orders.models import Vehicle
from wallet.models import Wallet
from orders.services import SmartPercelIntegration, IOrderService


class SmartParcelErrorHandlingTests(APITestCase):
    """Test suite for verifying SmartParcel API inner status code error handling."""

    def setUp(self) -> None:
        """Set up test users, wallets, vehicles, and client integrations."""
        self.merchant: User = User.objects.create_user(
            phone="08011112222",
            email="merchant@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Test Business",
            contact_name="Test Merchant",
        )
        self.client.force_authenticate(user=self.merchant)

        # Create wallet with balance
        self.wallet, _ = Wallet.objects.get_or_create(user=self.merchant)
        self.wallet.balance = Decimal("10000.00")
        self.wallet.save()

        # Create active vehicle
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

        self.integration = SmartPercelIntegration()

    @patch("requests.post")
    def test_create_parcel_integration_success(self, mock_post: MagicMock) -> None:
        """Verify integration client returns success when statuscode is '00'."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "statuscode": "00",
            "statusmessage": "New parcel request successful. Locker Number (5) has been reserved.",
            "parcel": {"trackingnumber": "SP123456"},
        }
        mock_post.return_value = mock_response

        ok, data = self.integration.create_parcel({"dummy": "payload"})
        self.assertTrue(ok)
        self.assertEqual(data["statuscode"], "00")

    @patch("requests.post")
    def test_create_parcel_integration_validation_error(self, mock_post: MagicMock) -> None:
        """Verify integration client returns False with inner statusmessage on validation errors ('04')."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parcel": None,
            "statuscode": "04",
            "statusmessage": "Missing Field : SizeID",
        }
        mock_post.return_value = mock_response

        ok, data = self.integration.create_parcel({"dummy": "payload"})
        self.assertFalse(ok)
        self.assertEqual(data, "Missing Field : SizeID")

    @patch("requests.post")
    def test_create_parcel_integration_business_error(self, mock_post: MagicMock) -> None:
        """Verify integration client returns False with inner statusmessage on business errors ('99')."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parcel": None,
            "statuscode": "99",
            "statusmessage": "No (Medium) locker available at (SmartParcel Sterling Bank Adeola Odeku).",
        }
        mock_post.return_value = mock_response

        ok, data = self.integration.create_parcel({"dummy": "payload"})
        self.assertFalse(ok)
        self.assertEqual(data, "No (Medium) locker available at (SmartParcel Sterling Bank Adeola Odeku).")

    @patch("requests.post")
    def test_create_parcel_view_error_handling(self, mock_post: MagicMock) -> None:
        """Verify the create parcel endpoint raises 502 Bad Gateway with the error message on inner API failure."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parcel": None,
            "statuscode": "99",
            "statusmessage": "Insufficient balance",
        }
        mock_post.return_value = mock_response

        url = reverse("orders:sp_create_parcel")
        payload = {
            "receiver_name": "Test Receiver",
            "receiver_phone": "08033334444",
            "sender_name": "Test Sender",
            "sender_phone": "08011112222",
            "box_id": "BOX_99",
            "locker_size_id": "SIZE_M",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("Insufficient balance", response.data["message"])

    @patch("requests.post")
    def test_process_parcel_delivery_service_error_handling(self, mock_post: MagicMock) -> None:
        """Verify IOrderService.process_parcel_delivery fails gracefully and returns 503 on inner API failure."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parcel": None,
            "statuscode": "99",
            "statusmessage": "No (Medium) locker available at (SmartParcel Sterling Bank Adeola Odeku).",
        }
        mock_post.return_value = mock_response

        # Mock the get_box_details endpoint to succeed
        mock_box_response = MagicMock()
        mock_box_response.ok = True
        mock_box_response.status_code = 200
        mock_box_response.json.return_value = {
            "data": {
                "boxaddress": "SmartParcel Sterling Bank Adeola Odeku"
            }
        }
        
        # Helper to return box details for boxes/info/ and failure for parcels/create/
        def side_effect(url: str, *args: Any, **kwargs: Any) -> MagicMock:
            if "boxes/info/" in url:
                return mock_box_response
            return mock_response
        
        mock_post.side_effect = side_effect

        service = IOrderService()
        ok, res = service.process_parcel_delivery(
            is_pickup=False,
            is_delivery=True,
            request_data={"box_id": "BOX_99", "dropoff_address": ""},
            parcel_payload={"dummy": "payload"},
        )

        self.assertFalse(ok)
        self.assertEqual(res["status_code"], 503)
        self.assertEqual(res["message"], "No (Medium) locker available at (SmartParcel Sterling Bank Adeola Odeku).")
