from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from orders.models import Order, Vehicle, Delivery
from authentication.models import MerchantEmailLog
from orders.tasks import send_transactional_email

User = get_user_model()


class MerchantProgressionEmailsTest(TestCase):
    """Test suite to verify that order status transitions trigger the correct merchant email notifications."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone="+2348000000001",
            email="merchant@example.com",
            password="password",
            usertype="Merchant",
        )
        self.vehicle = Vehicle.objects.create(
            name="Test Bike",
            max_weight_kg=50,
            base_price=300,
            base_fare=300,
            rate_per_km=40,
            rate_per_minute=2,
            is_active=True,
        )

    @patch("orders.tasks.send_transactional_email.delay")
    def test_order_creation_triggers_pending_email(self, mock_send_email: MagicMock) -> None:
        """Creating a new order should queue an F_Pending email task."""
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            pickup_latitude=6.45,
            pickup_longitude=3.39,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
        )

        mock_send_email.assert_called_once_with("F_Pending", str(order.id))

    @patch("orders.tasks.send_transactional_email.delay")
    def test_status_transitions_trigger_emails(self, mock_send_email: MagicMock) -> None:
        """Changing an order's status should trigger the corresponding progression email task."""
        # 1. Create order
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            pickup_latitude=6.45,
            pickup_longitude=3.39,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
        )
        mock_send_email.assert_called_once_with("F_Pending", str(order.id))
        mock_send_email.reset_mock()

        # 2. Transition to Assigned
        order.status = "Assigned"
        order.save()
        mock_send_email.assert_called_once_with("F_Assigned", str(order.id))
        mock_send_email.reset_mock()

        # 3. Transition to AssignmentAccepted
        order.status = "AssignmentAccepted"
        order.save()
        mock_send_email.assert_called_once_with("F_AssignmentAccepted", str(order.id))
        mock_send_mock = mock_send_email
        mock_send_mock.reset_mock()

        # 4. Transition to Started
        order.status = "Started"
        order.save()
        mock_send_email.assert_called_once_with("F1", str(order.id))
        mock_send_mock.reset_mock()

        # 5. Transition to PickedUp
        order.status = "PickedUp"
        order.save()
        mock_send_email.assert_called_once_with("F_PickedUp", str(order.id))
        mock_send_mock.reset_mock()

        # 6. Transition to Fulfilling
        order.status = "Fulfilling"
        order.save()
        mock_send_email.assert_called_once_with("F_Fulfilling", str(order.id))
        mock_send_mock.reset_mock()

        # 7. Transition to Arrived
        order.status = "Arrived"
        order.save()
        mock_send_email.assert_called_once_with("F_Arrived", str(order.id))
        mock_send_mock.reset_mock()

        # 8. Transition to Done
        order.status = "Done"
        order.save()
        mock_send_email.assert_called_once_with("F2", str(order.id))
        mock_send_mock.reset_mock()

    @patch("orders.tasks.send_transactional_email.delay")
    def test_saving_without_status_change_does_not_trigger_email(self, mock_send_email: MagicMock) -> None:
        """Saving an order without changing its status should not trigger a new email task."""
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            pickup_latitude=6.45,
            pickup_longitude=3.39,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
        )
        mock_send_email.assert_called_once_with("F_Pending", str(order.id))
        mock_send_email.reset_mock()

        # Modify something other than status
        order.notes = "Updated notes"
        order.save()

        mock_send_email.assert_not_called()

    @patch("orders.tasks._send_marketing_email")
    def test_send_transactional_email_task_execution(self, mock_send_marketing_email: MagicMock) -> None:
        """The Celery task should invoke _send_marketing_email with skip_daily_check=True."""
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            pickup_latitude=6.45,
            pickup_longitude=3.39,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
        )
        delivery = Delivery.objects.create(
            order=order,
            pickup_address="123 Test Street",
            dropoff_address="456 Test Road",
            receiver_name="Receiver Name",
            receiver_phone="+2348000000002",
        )

        # Clear any logs and reset call history created by the post_save signal during order creation
        MerchantEmailLog.objects.all().delete()
        mock_send_marketing_email.reset_mock()

        mock_send_marketing_email.return_value = True

        result = send_transactional_email("F_Pending", str(order.id))
        self.assertTrue(result)

        mock_send_marketing_email.assert_called_once()
        args, kwargs = mock_send_marketing_email.call_args
        self.assertEqual(args[0], self.user)
        self.assertEqual(args[1], "F_Pending")
        self.assertEqual(kwargs.get("skip_daily_check"), True)
