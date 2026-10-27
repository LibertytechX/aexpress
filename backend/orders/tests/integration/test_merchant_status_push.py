from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from dispatcher.models import (
    Merchant,
    MerchantDevice,
    MerchantNotification,
    MerchantNotificationSettings,
)
from dispatcher.tasks import send_merchant_notification
from orders.models import Order, Vehicle
from orders.signals import MERCHANT_STATUS_PUSHES

User = get_user_model()

DELAY = "dispatcher.tasks.send_merchant_notification.delay"


class MerchantOrderTestBase(TestCase):
    """Shared setup: a merchant user, a vehicle, and order helpers."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone="+2348000000011",
            email="push_merchant@example.com",
            password="password",
            usertype="Merchant",
        )
        self.merchant = Merchant.objects.get(user=self.user)
        self.vehicle = Vehicle.objects.create(
            name="Test Bike",
            max_weight_kg=50,
            base_price=300,
            base_fare=300,
            rate_per_km=40,
            rate_per_minute=2,
            is_active=True,
        )

    def _create_order(self, user=None, **extra) -> Order:
        return Order.objects.create(
            user=user or self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            pickup_latitude=6.45,
            pickup_longitude=3.39,
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
            **extra,
        )

    def _set_status(self, order: Order, new_status: str) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            order.status = new_status
            order.save()


class MerchantStatusPushTest(MerchantOrderTestBase):
    """Order status changes should queue the right push to the order's merchant."""

    @patch(DELAY)
    def test_each_status_queues_matching_push(self, mock_delay: MagicMock) -> None:
        """Every mapped status sends its own title, body, data and category."""
        order = self._create_order()

        for new_status, (title, body, category) in MERCHANT_STATUS_PUSHES.items():
            with self.subTest(status=new_status):
                mock_delay.reset_mock()
                self._set_status(order, new_status)

                mock_delay.assert_called_once_with(
                    str(self.merchant.id),
                    title,
                    body.format(order_number=order.order_number),
                    data={
                        "type": "order_status",
                        "order_number": order.order_number,
                        "status": new_status,
                    },
                    category=category,
                )

    @patch(DELAY)
    def test_order_creation_sends_no_push(self, mock_delay: MagicMock) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            self._create_order()

        mock_delay.assert_not_called()

    @patch(DELAY)
    def test_saving_without_status_change_sends_no_push(self, mock_delay: MagicMock) -> None:
        order = self._create_order()
        self._set_status(order, "Pickup")
        mock_delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            order.notes = "Updated notes"
            order.save()

        mock_delay.assert_not_called()

    @patch(DELAY)
    def test_unmapped_status_sends_no_push(self, mock_delay: MagicMock) -> None:
        order = self._create_order()

        self._set_status(order, "AssignmentAccepted")

        mock_delay.assert_not_called()

    @patch(DELAY)
    def test_relay_sub_order_sends_no_push(self, mock_delay: MagicMock) -> None:
        """Only the parent order notifies; its relay legs stay silent."""
        parent = self._create_order(is_relay_order=True)
        sub_order = self._create_order(parent_order=parent, is_relay_order=True)

        self._set_status(sub_order, "Pickup")

        mock_delay.assert_not_called()

    @patch(DELAY)
    def test_order_by_non_merchant_sends_no_push(self, mock_delay: MagicMock) -> None:
        customer = User.objects.create_user(
            phone="+2348000000012",
            email="push_customer@example.com",
            password="password",
            usertype="Customer",
        )
        order = self._create_order(user=customer)

        self._set_status(order, "Pickup")

        mock_delay.assert_not_called()


@patch("authentication.notifications.send_push")
class MerchantStatusPushDeliveryTest(MerchantOrderTestBase):
    """End to end: status change → inbox record → push to active devices only."""

    def setUp(self) -> None:
        super().setUp()
        MerchantDevice.objects.create(
            merchant=self.merchant, device_id="active-device", fcm_token="token-active"
        )
        MerchantDevice.objects.create(
            merchant=self.merchant,
            device_id="logged-out-device",
            fcm_token="token-inactive",
            is_active=False,
        )

    def _run_task_inline(self):
        return patch(
            DELAY,
            side_effect=lambda *args, **kwargs: send_merchant_notification(*args, **kwargs),
        )

    def test_push_saved_to_inbox_and_sent_to_active_device(self, mock_send_push: MagicMock) -> None:
        order = self._create_order()

        with self._run_task_inline():
            self._set_status(order, "Pickup")

        notification = MerchantNotification.objects.get(merchant=self.merchant)
        self.assertEqual(notification.title, "Package picked up")
        self.assertEqual(notification.data["order_number"], order.order_number)

        mock_send_push.assert_called_once()
        self.assertEqual(mock_send_push.call_args.args[0], "token-active")

    def test_master_switch_off_saves_to_inbox_without_push(self, mock_send_push: MagicMock) -> None:
        MerchantNotificationSettings.objects.update_or_create(
            merchant=self.merchant, defaults={"push_enabled": False}
        )
        order = self._create_order()

        with self._run_task_inline():
            self._set_status(order, "Fulfilling")

        self.assertEqual(MerchantNotification.objects.filter(merchant=self.merchant).count(), 1)
        mock_send_push.assert_not_called()

    def test_category_toggle_off_skips_only_that_category(self, mock_send_push: MagicMock) -> None:
        """Turning off order_completed silences "delivered" but not in-progress updates."""
        MerchantNotificationSettings.objects.update_or_create(
            merchant=self.merchant, defaults={"order_completed": False}
        )
        order = self._create_order()

        with self._run_task_inline():
            self._set_status(order, "Arrived")
            self._set_status(order, "Done")

        self.assertEqual(MerchantNotification.objects.filter(merchant=self.merchant).count(), 2)
        mock_send_push.assert_called_once()
        self.assertEqual(mock_send_push.call_args.args[1], "Rider at drop-off")
