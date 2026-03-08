from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone


class ReconcileRouteMetricsCommandTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from orders.models import Vehicle

        self.user = User.objects.create_user(
            phone="08011110000",
            email="reconcile@example.com",
            password="testpassword",
            usertype="Merchant",
            contact_name="Merchant",
            business_name="Test Biz",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike-Reconcile",
            max_weight_kg=10,
            base_price=Decimal("500.00"),
            base_fare=Decimal("200.00"),
            rate_per_km=Decimal("50.00"),
            rate_per_minute=Decimal("5.00"),
            min_fee=Decimal("500.00"),
            is_active=True,
        )

    @patch("orders.management.commands.reconcile_route_metrics.calculate_route")
    def test_flags_delivery_over_threshold_and_uses_sequential_legs(self, calc_mock):
        from orders.models import Order, Delivery

        calls = []

        def fake_calc(origin, destinations):
            calls.append((origin, destinations))
            dest = destinations[0]
            if dest["lat"] == 2.0:
                return {"distance_km": 5.0, "duration_minutes": 10}
            return {"distance_km": 5.0, "duration_minutes": 10}

        calc_mock.side_effect = fake_calc

        order = Order.objects.create(
            order_number="6159990",
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="Pickup",
            pickup_latitude=1.0,
            pickup_longitude=1.0,
            sender_name="Sender",
            sender_phone="08022223333",
            total_amount=Decimal("1000.00"),
            status="Done",
            completed_at=timezone.now(),
            distance_km=Decimal("10.00"),
            duration_minutes=20,
        )
        now = timezone.now()
        d1 = Delivery.objects.create(
            order=order,
            dropoff_address="D1",
            dropoff_latitude=2.0,
            dropoff_longitude=2.0,
            receiver_name="R1",
            receiver_phone="08000000001",
            status="Delivered",
            delivered_at=now,
            sequence=1,
            distance_km=Decimal("10.00"),  # expected 5.0 => 100% diff
            duration_minutes=10,
        )
        d2 = Delivery.objects.create(
            order=order,
            dropoff_address="D2",
            dropoff_latitude=3.0,
            dropoff_longitude=3.0,
            receiver_name="R2",
            receiver_phone="08000000002",
            status="Delivered",
            delivered_at=now,
            sequence=2,
            distance_km=Decimal("5.50"),  # expected 5.0 => 10% diff (within 20%)
            duration_minutes=10,
        )

        out = StringIO()
        call_command(
            "reconcile_route_metrics",
            date=timezone.localdate().isoformat(),
            threshold=0.2,
            stdout=out,
        )
        s = out.getvalue()

        self.assertIn("FLAG delivery", s)
        self.assertIn(str(d1.id), s)
        self.assertNotIn(str(d2.id), s)

        # Verify sequential legs: second leg origin = first dropoff
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], {"lat": 1.0, "lng": 1.0})
        self.assertEqual(calls[0][1], [{"lat": 2.0, "lng": 2.0}])
        self.assertEqual(calls[1][0], {"lat": 2.0, "lng": 2.0})
        self.assertEqual(calls[1][1], [{"lat": 3.0, "lng": 3.0}])

    @patch("orders.management.commands.reconcile_route_metrics.calculate_route")
    def test_no_flags_when_within_threshold(self, calc_mock):
        from orders.models import Order, Delivery

        calc_mock.return_value = {"distance_km": 5.0, "duration_minutes": 10}

        order = Order.objects.create(
            order_number="6159991",
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="Pickup",
            pickup_latitude=1.0,
            pickup_longitude=1.0,
            sender_name="Sender",
            sender_phone="08022223333",
            total_amount=Decimal("1000.00"),
            status="Done",
            completed_at=timezone.now(),
            distance_km=Decimal("5.00"),
            duration_minutes=10,
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="D1",
            dropoff_latitude=2.0,
            dropoff_longitude=2.0,
            receiver_name="R1",
            receiver_phone="08000000001",
            status="Delivered",
            delivered_at=timezone.now(),
            sequence=1,
            distance_km=Decimal("5.10"),  # 2% diff
            duration_minutes=10,
        )

        out = StringIO()
        call_command(
            "reconcile_route_metrics",
            date=timezone.localdate().isoformat(),
            threshold=0.2,
            stdout=out,
        )
        s = out.getvalue()

        self.assertNotIn("FLAG delivery", s)

