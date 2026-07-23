from typing import Any
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from orders.models import Order, Vehicle, Delivery
from orders.tasks import send_new_order_dispatcher_email_task

User: Any = get_user_model()


class DispatcherNotificationEmailTests(TestCase):
    """Test suite for dispatcher notification on new order creation."""

    merchant: User
    dispatcher1: User
    dispatcher2: User
    inactive_dispatcher: User
    rider: User
    vehicle: Vehicle

    def setUp(self) -> None:
        """Set up test data."""
        # Create merchant user (who creates the order)
        self.merchant = User.objects.create_user(
            phone="08011112222",
            email="merchant@example.com",
            password="testpassword",
            usertype="Merchant",
            business_name="Test Business",
            contact_name="Test Merchant",
        )

        # Create dispatcher users
        self.dispatcher1 = User.objects.create_user(
            phone="08055556666",
            email="dispatcher1@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher One",
        )
        self.dispatcher2 = User.objects.create_user(
            phone="08077778888",
            email="dispatcher2@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher Two",
        )

        # Create inactive/other users to ensure they are NOT sent emails
        self.inactive_dispatcher = User.objects.create_user(
            phone="08099990000",
            email="inactive@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Inactive Dispatcher",
            is_active=False,
        )
        self.rider = User.objects.create_user(
            phone="08022223333",
            email="rider@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Rider One",
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=100,
            base_price=Decimal("500.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("100.00"),
            rate_per_minute=Decimal("20.00"),
            min_fee=Decimal("500.00"),
            is_active=True,
        )

    @patch("orders.tasks.requests.post")
    @patch.dict("os.environ", {"MAILGUN_API_KEY": "fake-api-key", "MAILGUN_DOMAIN": "fake-domain.com"})
    def test_send_new_order_dispatcher_email_task(self, mock_post: MagicMock) -> None:
        """Verify that the task renders and sends the email to all active dispatchers with correct details."""
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create Order
        order: Order = Order.objects.create(
            user=self.merchant,
            pickup_address="123 Pickup St, Lagos",
            sender_name="John Doe",
            sender_phone="08011112222",
            vehicle=self.vehicle,
            total_amount=Decimal("1500.00"),
            payment_method="wallet",
            status="Pending",
        )

        # Create Delivery
        delivery: Delivery = Delivery.objects.create(
            order=order,
            pickup_address="123 Pickup St, Lagos",
            dropoff_address="456 Dropoff Rd, Lagos",
            receiver_name="Jane Smith",
            receiver_phone="08033334444",
            package_type="Box",
        )

        # Reset mock calls triggered by signals during order creation
        mock_post.reset_mock()

        # Call task directly
        result: bool = send_new_order_dispatcher_email_task(str(order.id))
        self.assertTrue(result)

        # Assert requests.post was called for each active dispatcher
        self.assertEqual(mock_post.call_count, 2)

        # Check call arguments for the first active dispatcher
        called_emails: list[str] = [call.kwargs["data"]["to"][0] for call in mock_post.call_args_list]
        self.assertIn("dispatcher1@example.com", called_emails)
        self.assertIn("dispatcher2@example.com", called_emails)
        self.assertNotIn("inactive@example.com", called_emails)
        self.assertNotIn("rider@example.com", called_emails)

        # Verify subject and email body content
        first_call_data: dict[str, Any] = mock_post.call_args_list[0].kwargs["data"]
        self.assertIn(f"Order #{order.order_number}", first_call_data["subject"])
        self.assertIn("123 Pickup St, Lagos", first_call_data["html"])
        self.assertIn("456 Dropoff Rd, Lagos", first_call_data["html"])

    @patch("orders.tasks.send_new_order_dispatcher_email_task.delay")
    def test_order_creation_triggers_signal(self, mock_task_delay: MagicMock) -> None:
        """Verify that creating an order triggers the post_save signal which calls the celery task delay."""
        order: Order = Order.objects.create(
            user=self.merchant,
            pickup_address="123 Pickup St, Lagos",
            sender_name="John Doe",
            sender_phone="08011112222",
            vehicle=self.vehicle,
            total_amount=Decimal("1500.00"),
            payment_method="wallet",
            status="Pending",
        )
        mock_task_delay.assert_called_once_with(str(order.id))
