from django.test import TestCase
from unittest.mock import patch
from decimal import Decimal
import datetime

from rest_framework import serializers
from rest_framework.test import APIClient
from django.core.management import call_command
from django.utils import timezone


class _Req:
    def __init__(self, user):
        self.user = user


class OrderCreateSerializerGeocodingTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from orders.models import Vehicle

        self.dispatcher_user = User.objects.create_user(
            phone="08099990000",
            email="dispatcher@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )

        # Minimal active vehicle to satisfy OrderCreateSerializer vehicle resolution
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

    @patch("orders.utils.geocode_address")
    def test_create_geocodes_missing_coords(self, geocode_mock):
        from orders.models import Delivery
        from .serializers import OrderCreateSerializer

        geocode_mock.side_effect = [
            {"lat": 6.50, "lng": 3.30},  # pickup
            {"lat": 6.60, "lng": 3.40},  # dropoff
        ]

        payload = {
            "pickup": "Some Pickup Address, Lagos",
            "dropoff": "Some Dropoff Address, Lagos",
            "senderName": "Sender",
            "senderPhone": "08011112222",
            "receiverName": "Receiver",
            "receiverPhone": "08033334444",
            "vehicle": "Bike",
            "packageType": "Box",
            "price": 1000,
            "cod": 0,
            "distance_km": 1.2,
            "duration_minutes": 10,
            "is_relay_order": False,
            "pickup_lat": None,
            "pickup_lng": None,
            "dropoff_lat": None,
            "dropoff_lng": None,
        }

        ser = OrderCreateSerializer(
            data=payload, context={"request": _Req(self.dispatcher_user)}
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        order = ser.save()

        order.refresh_from_db()
        self.assertAlmostEqual(float(order.pickup_latitude), 6.50, places=6)
        self.assertAlmostEqual(float(order.pickup_longitude), 3.30, places=6)

        d = Delivery.objects.get(order=order)
        self.assertAlmostEqual(float(d.dropoff_latitude), 6.60, places=6)
        self.assertAlmostEqual(float(d.dropoff_longitude), 3.40, places=6)

        # Persist per-delivery route stats (mirrors payload)
        self.assertAlmostEqual(float(d.distance_km), 1.2, places=2)
        self.assertEqual(d.duration_minutes, 10)

    @patch("orders.utils.geocode_address", return_value=None)
    def test_relay_order_requires_geocoded_coords(self, geocode_mock):
        from .serializers import OrderCreateSerializer

        payload = {
            "pickup": "Unknown Pickup",
            "dropoff": "Unknown Dropoff",
            "senderName": "Sender",
            "senderPhone": "08011112222",
            "receiverName": "Receiver",
            "receiverPhone": "08033334444",
            "vehicle": "Bike",
            "packageType": "Box",
            "price": 1000,
            "cod": 0,
            "distance_km": 1.2,
            "duration_minutes": 10,
            "is_relay_order": True,
            "pickup_lat": None,
            "pickup_lng": None,
            "dropoff_lat": None,
            "dropoff_lng": None,
        }

        ser = OrderCreateSerializer(
            data=payload, context={"request": _Req(self.dispatcher_user)}
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        with self.assertRaises(serializers.ValidationError):
            ser.save()

    def test_create_accepts_short_rider_id(self):
        """Regression: frontend sends Rider.rider_id (e.g. '168817'), not UUID."""
        from authentication.models import User
        from .models import Rider
        from .serializers import OrderCreateSerializer

        rider_user = User.objects.create_user(
            phone="08088887777",
            email="rider168817@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Rider 168817",
        )
        Rider.objects.create(user=rider_user, rider_id="168817")

        payload = {
            "pickup": "Some Pickup Address, Lagos",
            "dropoff": "Some Dropoff Address, Lagos",
            "senderName": "Sender",
            "senderPhone": "08011112222",
            "receiverName": "Receiver",
            "receiverPhone": "08033334444",
            "vehicle": "Bike",
            "packageType": "Box",
            "price": 1000,
            "cod": 0,
            "distance_km": 1.2,
            "duration_minutes": 10,
            "is_relay_order": False,
            # Provide coords to avoid any external geocoding calls
            "pickup_lat": 6.50,
            "pickup_lng": 3.30,
            "dropoff_lat": 6.60,
            "dropoff_lng": 3.40,
            "riderId": "168817",
        }

        ser = OrderCreateSerializer(
            data=payload, context={"request": _Req(self.dispatcher_user)}
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        order = ser.save()
        self.assertIsNotNone(order.rider)
        self.assertEqual(order.rider.rider_id, "168817")
        self.assertEqual(order.status, "Assigned")

        from orders.models import Delivery

        d = Delivery.objects.get(order=order)
        self.assertAlmostEqual(float(d.distance_km), 1.2, places=2)
        self.assertEqual(d.duration_minutes, 10)


class OrderSerializerRouteStatsTests(TestCase):
    def test_order_serializer_uses_persisted_distance_and_time(self):
        from authentication.models import User
        from orders.models import Order, Delivery, Vehicle
        from .serializers import OrderSerializer

        user = User.objects.create_user(
            phone="08055554444",
            email="dispatcher_stats@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )

        vehicle = Vehicle.objects.create(
            name="Bike-Stats",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )

        order = Order.objects.create(
            order_number="6159555",
            user=user,
            vehicle=vehicle,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            status="Pending",
            distance_km=Decimal("5.2"),
            duration_minutes=25,
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="Dropoff",
            receiver_name="Receiver",
            receiver_phone="08033334444",
        )

        data = OrderSerializer(order).data
        self.assertEqual(data.get("distance"), "5.20 km")
        self.assertEqual(data.get("time"), "25 mins")


class VehicleDistanceTelemetryTests(TestCase):
    def test_extract_total_distance_supports_multiple_keys(self):
        from .management.commands.sync_bike_telemetry import _extract_total_distance

        self.assertEqual(_extract_total_distance({"total_distance": "12.34"}), Decimal("12.34"))
        self.assertEqual(_extract_total_distance({"travelled": 56.78}), Decimal("56.78"))
        self.assertEqual(_extract_total_distance({"odometer": "90"}), Decimal("90"))
        self.assertIsNone(_extract_total_distance({"nope": 1}))

    def test_build_tracking_row_skips_invalid_coords_and_requires_travelled(self):
        from .models import VehicleAsset
        from .management.commands.sync_bike_telemetry import _build_tracking_row

        asset = VehicleAsset.objects.create(
            asset_id="AXT000001",
            plate_number="TEST-PLATE-001",
            vehicle_type="bike",
            total_distance=Decimal("10.00"),
            unit_of_distance="km",
        )

        # Invalid coords (0,0) must be skipped even if distance exists
        row = _build_tracking_row(asset, {"lat": 0, "lng": 0, "total_distance": "11.00", "unit_of_distance": "km"})
        self.assertIsNone(row)

        # Valid coords should build a row (travelled falls back to asset.total_distance)
        row = _build_tracking_row(asset, {"lat": "6.50", "lng": "3.30"})
        self.assertIsNotNone(row)
        self.assertEqual(row.travelled, Decimal("10.00"))
        self.assertEqual(row.unit_of_distance, "km")

    def test_upsert_device_does_not_overwrite_distance_when_provider_omits(self):
        from .models import VehicleAsset
        from .management.commands.sync_bike_telemetry import _upsert_device

        VehicleAsset.objects.create(
            asset_id="AXT000002",
            plate_number="TEST-PLATE-002",
            vehicle_type="bike",
            provider_id="dev-1",
            total_distance=Decimal("123.45"),
            unit_of_distance="km",
        )

        # No total_distance/unit_of_distance in payload => must keep existing DB values
        result, asset = _upsert_device(
            {
                "id": "dev-1",
                "name": "Device 1",
                "online": True,
                "lat": "6.5000000",
                "lng": "3.3000000",
                "speed": 10,
            },
            status_code=200,
            snippet="ok",
            dry_run=False,
        )
        self.assertIn(result, ("updated", "created"))
        self.assertIsNotNone(asset)
        asset.refresh_from_db()
        self.assertEqual(asset.total_distance, Decimal("123.45"))
        self.assertEqual(asset.unit_of_distance, "km")


class OrderPriceUpdateEndpointTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from orders.models import Vehicle

        self.user = User.objects.create_user(
            phone="08077776666",
            email="dispatcher_price@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike-Price",
            max_weight_kg=10,
            base_price=500,
            base_fare=0,
            rate_per_km=0,
            rate_per_minute=0,
            min_fee=0,
            is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _create_order(self, **kwargs):
        from orders.models import Order, Delivery

        order = Order.objects.create(
            order_number=kwargs.get("order_number", "6159001"),
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=kwargs.get("total_amount", Decimal("1000.00")),
            payment_status=kwargs.get("payment_status", "Pending"),
            escrow_released=kwargs.get("escrow_released", False),
            status=kwargs.get("status", "Pending"),
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="Dropoff",
            receiver_name="Receiver",
            receiver_phone="08033334444",
        )
        return order

    def test_update_price_updates_total_amount(self):
        order = self._create_order(order_number="6159002")
        res = self.client.patch(
            f"/api/dispatch/orders/{order.order_number}/update-price/",
            {"amount": "1760.00"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("1760.00"))
        self.assertEqual(str(res.data.get("amount")), "1760.00")

    def test_update_price_rejects_paid_or_released(self):
        order_paid = self._create_order(order_number="6159003", payment_status="Paid")
        res = self.client.patch(
            f"/api/dispatch/orders/{order_paid.order_number}/update-price/",
            {"amount": "1760.00"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

        order_rel = self._create_order(order_number="6159004", escrow_released=True)
        res2 = self.client.patch(
            f"/api/dispatch/orders/{order_rel.order_number}/update-price/",
            {"amount": "1760.00"},
            format="json",
        )
        self.assertEqual(res2.status_code, 400)


class VehicleDistanceTodayCommandTests(TestCase):
    def _mk_asset(self, plate: str, **kwargs):
        from .models import VehicleAsset

        return VehicleAsset.objects.create(
            plate_number=plate,
            vehicle_type="bike",
            total_distance=kwargs.get("total_distance"),
            unit_of_distance=kwargs.get("unit_of_distance"),
            distance_today=kwargs.get("distance_today"),
        )

    def _mk_tracking(self, asset, travelled: Decimal, created_at):
        from .models import VehicleTracking

        row = VehicleTracking.objects.create(
            vehicle_asset=asset,
            latitude=Decimal("6.5000000"),
            longitude=Decimal("3.3000000"),
            travelled=travelled,
            unit_of_distance="km",
        )
        VehicleTracking.objects.filter(id=row.id).update(created_at=created_at)

    def test_compute_distance_today_uses_first_and_last_snapshot(self):
        asset = self._mk_asset("TEST-PLATE-DAY-1")
        day = timezone.localdate()
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(
            datetime.datetime.combine(day, datetime.time.min), tz
        )

        self._mk_tracking(asset, Decimal("100.00"), start + datetime.timedelta(hours=1))
        self._mk_tracking(asset, Decimal("112.00"), start + datetime.timedelta(hours=5))

        call_command("compute_distance_today", date=day.isoformat())
        asset.refresh_from_db()
        self.assertEqual(asset.distance_today, Decimal("12.00"))

    def test_compute_distance_today_clamps_negative_delta(self):
        asset = self._mk_asset("TEST-PLATE-DAY-2")
        day = timezone.localdate()
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(
            datetime.datetime.combine(day, datetime.time.min), tz
        )

        self._mk_tracking(asset, Decimal("200.00"), start + datetime.timedelta(hours=1))
        self._mk_tracking(asset, Decimal("50.00"), start + datetime.timedelta(hours=2))

        call_command("compute_distance_today", date=day.isoformat())
        asset.refresh_from_db()
        self.assertEqual(asset.distance_today, Decimal("0.00"))

    def test_compute_distance_today_reset_missing(self):
        asset_no_data = self._mk_asset(
            "TEST-PLATE-DAY-3", distance_today=Decimal("5.00")
        )
        day = timezone.localdate()

        call_command(
            "compute_distance_today",
            date=day.isoformat(),
            reset_missing=True,
        )
        asset_no_data.refresh_from_db()
        self.assertEqual(asset_no_data.distance_today, Decimal("0.00"))


class VehicleAssetOrdersTodayEndpointTests(TestCase):
    def setUp(self):
        from authentication.models import User

        self.user = User.objects.create_user(
            phone="08088880000",
            email="dispatcher_vehicle_assets@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_vehicle_assets_list_includes_orders_today(self):
        from authentication.models import User
        from dispatcher.models import VehicleAsset, Rider
        from orders.models import Vehicle, Order

        vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=0,
            rate_per_km=0,
            rate_per_minute=0,
            min_fee=0,
            is_active=True,
        )

        asset = VehicleAsset.objects.create(
            plate_number="TP-ORD-TDY-1",
            vehicle_type="bike",
            unit_of_distance="km",
        )

        rider_user = User.objects.create_user(
            phone="08088880001",
            email="rider_vehicle_assets@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Rider",
        )
        rider = Rider.objects.create(user=rider_user, vehicle_asset=asset)

        day = timezone.localdate()
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(
            datetime.datetime.combine(day, datetime.time.min), tz
        )

        # 2 completed today
        Order.objects.create(
            order_number="6159901",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Done",
            completed_at=start + datetime.timedelta(hours=1),
        )
        Order.objects.create(
            order_number="6159902",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Done",
            completed_at=start + datetime.timedelta(hours=2),
        )

        # completed yesterday (should not count)
        Order.objects.create(
            order_number="6159903",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Done",
            completed_at=start - datetime.timedelta(hours=1),
        )

        # not done today (should not count)
        Order.objects.create(
            order_number="6159904",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Assigned",
            completed_at=start + datetime.timedelta(hours=3),
        )

        res = self.client.get("/api/dispatch/vehicle-assets/")
        self.assertEqual(res.status_code, 200, res.data)

        data = res.data
        if isinstance(data, dict) and "results" in data:
            rows = data["results"]
        else:
            rows = data

        row = next((r for r in rows if str(r.get("id")) == str(asset.id)), None)
        self.assertIsNotNone(row)
        self.assertEqual(row.get("orders_today"), 2)

    def test_vehicle_assets_orders_today_falls_back_to_delivery_delivered_at(self):
        """If an order is marked Done but completed_at is missing, we still count it
        when any related Delivery.delivered_at is within the local-day window.
        """

        from authentication.models import User
        from dispatcher.models import VehicleAsset, Rider
        from orders.models import Vehicle, Order, Delivery

        vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=0,
            rate_per_km=0,
            rate_per_minute=0,
            min_fee=0,
            is_active=True,
        )

        asset = VehicleAsset.objects.create(
            plate_number="TP-ORD-TDY-2",
            vehicle_type="bike",
            unit_of_distance="km",
        )

        rider_user = User.objects.create_user(
            phone="08088880002",
            email="rider_vehicle_assets_2@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Rider 2",
        )
        rider = Rider.objects.create(user=rider_user, vehicle_asset=asset)

        day = timezone.localdate()
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min), tz)

        order = Order.objects.create(
            order_number="6159910",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Done",
            completed_at=None,
        )

        Delivery.objects.create(
            order=order,
            dropoff_address="Dropoff",
            receiver_name="Receiver",
            receiver_phone="08033334444",
            status="Delivered",
            delivered_at=start + datetime.timedelta(hours=1),
            sequence=1,
        )

        res = self.client.get("/api/dispatch/vehicle-assets/")
        self.assertEqual(res.status_code, 200, res.data)

        data = res.data
        if isinstance(data, dict) and "results" in data:
            rows = data["results"]
        else:
            rows = data

        row = next((r for r in rows if str(r.get("id")) == str(asset.id)), None)
        self.assertIsNotNone(row)
        self.assertEqual(row.get("orders_today"), 1)

    def test_vehicle_assets_orders_today_falls_back_to_order_updated_at_when_timestamps_missing(self):
        """If an order is marked Done/Delivered but both Order.completed_at and
        Delivery.delivered_at are missing, count it for today using Order.updated_at
        *only* when Delivery.status indicates completion.
        """

        from authentication.models import User
        from dispatcher.models import VehicleAsset, Rider
        from orders.models import Vehicle, Order, Delivery

        vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=0,
            rate_per_km=0,
            rate_per_minute=0,
            min_fee=0,
            is_active=True,
        )

        asset = VehicleAsset.objects.create(
            plate_number="TP-ORD-TDY-3",
            vehicle_type="bike",
            unit_of_distance="km",
        )

        rider_user = User.objects.create_user(
            phone="08088880003",
            email="rider_vehicle_assets_3@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Rider 3",
        )
        rider = Rider.objects.create(user=rider_user, vehicle_asset=asset)

        day = timezone.localdate()
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min), tz)

        order = Order.objects.create(
            order_number="6159920",
            user=self.user,
            vehicle=vehicle,
            rider=rider,
            pickup_address="Pickup",
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            escrow_released=False,
            status="Done",
            completed_at=None,
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="Dropoff",
            receiver_name="Receiver",
            receiver_phone="08033334444",
            status="Delivered",
            delivered_at=None,
            sequence=1,
        )

        # Force updated_at into the current local-day window.
        Order.objects.filter(id=order.id).update(updated_at=start + datetime.timedelta(hours=1))

        res = self.client.get("/api/dispatch/vehicle-assets/")
        self.assertEqual(res.status_code, 200, res.data)

        data = res.data
        if isinstance(data, dict) and "results" in data:
            rows = data["results"]
        else:
            rows = data

        row = next((r for r in rows if str(r.get("id")) == str(asset.id)), None)
        self.assertIsNotNone(row)
        self.assertEqual(row.get("orders_today"), 1)

