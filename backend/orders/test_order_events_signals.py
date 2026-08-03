from typing import Any
from django.contrib.auth import get_user_model
from django.test import TestCase
from orders.models import Order, OrderEvent, Vehicle
from orders.signals import order_event_signal

User = get_user_model()


class OrderEventSignalsTestCase(TestCase):
    """Test suite for automated and custom OrderEvent signal logging."""

    def setUp(self) -> None:
        """Set up test user, vehicle, and base objects."""
        self.user = User.objects.create_user(
            phone="08012345678",
            email="testuser@example.com",
            password="testpassword123",
        )

        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500.0,
            base_fare=500.0,
            rate_per_km=100.0,
        )


    def test_order_creation_triggers_order_event_signal(self) -> None:
        """Verify that creating an Order automatically logs an 'order_created' OrderEvent."""
        order: Order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            total_amount=1500.0,
            status="Pending",
        )

        event: OrderEvent | None = OrderEvent.objects.filter(
            order=order, event="order_created"
        ).first()

        self.assertIsNotNone(event)
        if event:
            self.assertEqual(event.event, "order_created")
            self.assertIn(f"Order #{order.order_number}", event.description)
            self.assertEqual(event.created_by, self.user)

    def test_order_status_change_triggers_order_event_signal(self) -> None:
        """Verify that updating an Order's status automatically logs a status change OrderEvent."""
        order: Order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            total_amount=1500.0,
            status="Pending",
        )

        # Transition status from Pending -> Assigned
        order.status = "Assigned"
        order.save()

        status_event: OrderEvent | None = OrderEvent.objects.filter(
            order=order, event="order_status_assigned"
        ).first()

        self.assertIsNotNone(status_event)
        if status_event:
            self.assertEqual(status_event.old_value, "Pending")
            self.assertEqual(status_event.new_value, "Assigned")
            self.assertIn("Pending to Assigned", status_event.description)

    def test_custom_order_event_signal_dispatch(self) -> None:
        """Verify that dispatching order_event_signal creates a custom OrderEvent."""
        order: Order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            total_amount=1500.0,
            status="Pending",
        )

        order_event_signal.send(
            sender=self.__class__,
            order=order,
            event="custom_audit_event",
            description="Custom audit description",
            old_value="1000",
            new_value="1500",
            created_by=self.user,
        )

        custom_event: OrderEvent | None = OrderEvent.objects.filter(
            order=order, event="custom_audit_event"
        ).first()

        self.assertIsNotNone(custom_event)
        if custom_event:
            self.assertEqual(custom_event.description, "Custom audit description")
            self.assertEqual(custom_event.old_value, "1000")
            self.assertEqual(custom_event.new_value, "1500")
            self.assertEqual(custom_event.created_by, self.user)
