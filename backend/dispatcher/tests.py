from django.test import TestCase
from unittest.mock import patch
from decimal import Decimal
import datetime

from rest_framework import serializers
from rest_framework.test import APIClient
from django.contrib import admin
from django.contrib.admin.utils import label_for_field, lookup_field
from django.core.management import call_command
from django.urls import reverse
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

        self.assertEqual(
            _extract_total_distance({"total_distance": "12.34"}), Decimal("12.34")
        )
        self.assertEqual(
            _extract_total_distance({"travelled": 56.78}), Decimal("56.78")
        )
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
        row = _build_tracking_row(
            asset,
            {"lat": 0, "lng": 0, "total_distance": "11.00", "unit_of_distance": "km"},
        )
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


class RiderAdminLookupTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from .admin import RiderAdmin
        from .models import Rider

        self.rider_model = Rider
        self.model_admin = RiderAdmin(Rider, admin.site)
        self.user = User.objects.create_user(
            phone="08055550001",
            email="rider_admin_lookup@example.com",
            password="testpassword",
            usertype="Rider",
            contact_name="Lookup Rider",
        )
        self.rider = self.user.rider_profile
        self.rider.rider_id = "654321"
        self.rider.save(update_fields=["rider_id"])

    def test_model_exposes_yesterday_distance_covered(self):
        self.assertTrue(hasattr(self.rider, "yesterday_distance_covered"))
        self.assertEqual(self.rider.yesterday_distance_covered(), 0.00)

    def test_admin_lookup_resolves_yesterday_distance_covered(self):
        label = label_for_field(
            "yesterday_distance_covered", self.rider_model, self.model_admin
        )
        self.assertEqual(label, "Prev Day Distance (km)")

        field, attr, value = lookup_field(
            "yesterday_distance_covered", self.rider, self.model_admin
        )
        self.assertIsNone(field)
        self.assertTrue(callable(attr))
        self.assertEqual(value, 0.00)

    def test_admin_changelist_renders(self):
        from authentication.models import User

        admin_user = User.objects.create_user(
            phone="08055550002",
            email="dispatcher_admin_lookup@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Admin User",
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=["is_staff", "is_superuser"])

        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:dispatcher_rider_changelist"))

        self.assertEqual(response.status_code, 200)


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
        start = timezone.make_aware(
            datetime.datetime.combine(day, datetime.time.min), tz
        )

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

    def test_vehicle_assets_orders_today_falls_back_to_order_updated_at_when_timestamps_missing(
        self,
    ):
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
        start = timezone.make_aware(
            datetime.datetime.combine(day, datetime.time.min), tz
        )

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
        Order.objects.filter(id=order.id).update(
            updated_at=start + datetime.timedelta(hours=1)
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


class GenerateRelayLegsSyncTests(TestCase):
    KM_PER_DEGREE_LNG = 111.1949

    def setUp(self):
        from authentication.models import User
        from dispatcher import tasks as dispatcher_tasks
        from orders.models import Vehicle

        self.user = User.objects.create_user(
            phone="08077770000",
            email="relay-dispatcher@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Relay Dispatcher",
        )
        self.vehicle = Vehicle.objects.create(
            name="Relay Bike",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )
        dispatcher_tasks._RELAY_NODES_CACHE["nodes"] = None
        dispatcher_tasks._RELAY_NODES_CACHE["ts"] = 0

    def _lng_for_km(self, km):
        return km / self.KM_PER_DEGREE_LNG

    def _create_order(self, total_km):
        from orders.models import Delivery, Order

        order = Order.objects.create(
            order_number=f"REL-{int(total_km * 10)}",
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="Origin",
            pickup_latitude=0,
            pickup_longitude=0,
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("9000.00"),
            payment_status="Pending",
            is_relay_order=True,
            routing_status=Order.RoutingStatus.PENDING,
        )
        Delivery.objects.create(
            order=order,
            dropoff_address="Destination",
            dropoff_latitude=0,
            dropoff_longitude=self._lng_for_km(total_km),
            receiver_name="Receiver",
            receiver_phone="08033334444",
            status="Pending",
            sequence=1,
        )
        return order

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._directions_legs", return_value=None)
    @patch("dispatcher.tasks._nearest_rider_to")
    def test_generate_relay_legs_builds_continuous_20km_chain(
        self, nearest_rider_mock, _directions_mock, _emit_activity_mock
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        rider_calls = []

        def record_rider_lookup(lat, lng, hub=None):
            if hub is None:
                rider_calls.append((float(lat), float(lng)))
            return None

        nearest_rider_mock.side_effect = record_rider_lookup

        hub_one = RelayNode.objects.create(
            name="Hub 1",
            address="20km Hub",
            latitude=0,
            longitude=self._lng_for_km(20),
            is_active=True,
        )
        hub_two = RelayNode.objects.create(
            name="Hub 2",
            address="40km Hub",
            latitude=0,
            longitude=self._lng_for_km(40),
            is_active=True,
        )
        hub_three = RelayNode.objects.create(
            name="Hub 3",
            address="60km Hub",
            latitude=0,
            longitude=self._lng_for_km(60),
            is_active=True,
        )
        order = self._create_order(total_km=80)

        success = generate_relay_legs_sync(order.id)

        self.assertTrue(success)
        order.refresh_from_db()
        legs = list(order.legs.order_by("leg_number"))

        self.assertEqual(order.routing_status, order.RoutingStatus.READY)
        self.assertEqual(order.relay_legs_count, 4)
        self.assertEqual(len(legs), 4)

        self.assertIsNone(legs[0].start_relay_node)
        self.assertEqual(legs[0].end_relay_node_id, hub_one.id)
        self.assertEqual(legs[1].start_relay_node_id, hub_one.id)
        self.assertEqual(legs[1].end_relay_node_id, hub_two.id)
        self.assertEqual(legs[2].start_relay_node_id, hub_two.id)
        self.assertEqual(legs[2].end_relay_node_id, hub_three.id)
        self.assertEqual(legs[3].start_relay_node_id, hub_three.id)
        self.assertIsNone(legs[3].end_relay_node)

        self.assertTrue(all(leg.distance_km <= 20.0 for leg in legs))
        self.assertEqual(len(rider_calls), 4)
        self.assertAlmostEqual(rider_calls[0][1], 0.0, places=4)
        self.assertAlmostEqual(rider_calls[1][1], float(hub_one.longitude), places=4)
        self.assertAlmostEqual(rider_calls[2][1], float(hub_two.longitude), places=4)
        self.assertAlmostEqual(rider_calls[3][1], float(hub_three.longitude), places=4)

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._directions_legs", return_value=None)
    @patch("dispatcher.tasks._nearest_rider_to", return_value=None)
    def test_generate_relay_legs_prefers_farthest_forward_hub_within_20km(
        self, _nearest_rider_mock, _directions_mock, _emit_activity_mock
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        nearer_hub = RelayNode.objects.create(
            name="Nearer Hub",
            address="12km Hub",
            latitude=0,
            longitude=self._lng_for_km(12),
            is_active=True,
        )
        forward_hub = RelayNode.objects.create(
            name="Forward Hub",
            address="19km Hub",
            latitude=0,
            longitude=self._lng_for_km(19),
            is_active=True,
        )
        final_hub = RelayNode.objects.create(
            name="Final Hub",
            address="37km Hub",
            latitude=0,
            longitude=self._lng_for_km(37),
            is_active=True,
        )
        order = self._create_order(total_km=55)

        success = generate_relay_legs_sync(order.id)

        self.assertTrue(success)
        order.refresh_from_db()
        legs = list(order.legs.order_by("leg_number"))

        self.assertEqual(order.routing_status, order.RoutingStatus.READY)
        self.assertEqual(len(legs), 3)
        self.assertEqual(legs[0].end_relay_node_id, forward_hub.id)
        self.assertEqual(legs[1].start_relay_node_id, forward_hub.id)
        self.assertEqual(legs[1].end_relay_node_id, final_hub.id)
        self.assertNotEqual(legs[0].end_relay_node_id, nearer_hub.id)
        self.assertTrue(all(leg.distance_km <= 20.0 for leg in legs))

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._directions_legs", return_value=None)
    @patch("dispatcher.tasks._nearest_rider_to", return_value=None)
    def test_generate_relay_legs_falls_back_to_nearest_forward_hub_when_no_20km_hub_exists(
        self, _nearest_rider_mock, _directions_mock, _emit_activity_mock
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        first_hub = RelayNode.objects.create(
            name="Fallback Hub",
            address="23km Hub",
            latitude=0,
            longitude=self._lng_for_km(23),
            is_active=True,
        )
        second_hub = RelayNode.objects.create(
            name="Forward Hub",
            address="43km Hub",
            latitude=0,
            longitude=self._lng_for_km(43),
            is_active=True,
        )
        order = self._create_order(total_km=63)

        success = generate_relay_legs_sync(order.id)

        self.assertTrue(success)
        order.refresh_from_db()
        legs = list(order.legs.order_by("leg_number"))

        self.assertEqual(order.routing_status, order.RoutingStatus.READY)
        self.assertEqual(len(legs), 3)
        self.assertEqual(legs[0].end_relay_node_id, first_hub.id)
        self.assertEqual(legs[1].start_relay_node_id, first_hub.id)
        self.assertEqual(legs[1].end_relay_node_id, second_hub.id)
        self.assertGreater(legs[0].distance_km, 20.0)
        self.assertLessEqual(legs[1].distance_km, 20.0)
        self.assertLessEqual(legs[2].distance_km, 20.0)

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._nearest_rider_to", return_value=None)
    @patch("dispatcher.tasks._directions_legs")
    def test_generate_relay_legs_uses_route_distance_for_relay_trigger(
        self, directions_mock, _nearest_rider_mock, _emit_activity_mock
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        hub = RelayNode.objects.create(
            name="Bridge Hub",
            address="10km Hub",
            latitude=0,
            longitude=self._lng_for_km(10),
            is_active=True,
        )
        order = self._create_order(total_km=19)

        def directions_side_effect(origin, points):
            if len(points) == 1:
                if float(origin["lng"]) == 0.0:
                    return [(53.0, 120)]
                return [(15.0, 36)]

            if len(points) == 2:
                return [(10.0, 24), (15.0, 36)]

            return None

        directions_mock.side_effect = directions_side_effect

        success = generate_relay_legs_sync(order.id)

        self.assertTrue(success)
        order.refresh_from_db()
        legs = list(order.legs.order_by("leg_number"))

        self.assertEqual(order.routing_status, order.RoutingStatus.READY)
        self.assertEqual(len(legs), 2)
        self.assertEqual(legs[0].end_relay_node_id, hub.id)
        self.assertIsNone(legs[1].end_relay_node)
        self.assertEqual(legs[0].distance_km, 10.0)
        self.assertEqual(legs[1].distance_km, 15.0)

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._nearest_rider_to", return_value=None)
    @patch("dispatcher.tasks._route_distance_km")
    @patch("dispatcher.tasks._directions_legs")
    def test_generate_relay_legs_uses_route_distance_when_selecting_each_hop(
        self,
        directions_mock,
        route_distance_mock,
        _nearest_rider_mock,
        _emit_activity_mock,
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        ikorodu = RelayNode.objects.create(
            name="Ikorodu Hub",
            address="Ikorodu",
            latitude=0,
            longitude=self._lng_for_km(5),
            is_active=True,
        )
        mile_12 = RelayNode.objects.create(
            name="Mile 12 Hub",
            address="Mile 12",
            latitude=0,
            longitude=self._lng_for_km(10),
            is_active=True,
        )
        osapa = RelayNode.objects.create(
            name="Osapa Hub",
            address="Osapa",
            latitude=-0.05,
            longitude=self._lng_for_km(14),
            is_active=True,
        )
        order = self._create_order(total_km=19)
        dropoff = order.deliveries.first()

        def point_key(point):
            return (round(float(point["lat"]), 6), round(float(point["lng"]), 6))

        pickup_key = (0.0, 0.0)
        ikorodu_key = point_key({"lat": ikorodu.latitude, "lng": ikorodu.longitude})
        mile_12_key = point_key({"lat": mile_12.latitude, "lng": mile_12.longitude})
        osapa_key = point_key({"lat": osapa.latitude, "lng": osapa.longitude})
        dropoff_key = point_key(
            {"lat": dropoff.dropoff_latitude, "lng": dropoff.dropoff_longitude}
        )

        route_distances = {
            (pickup_key, dropoff_key): 53.0,
            (pickup_key, ikorodu_key): 8.0,
            (pickup_key, mile_12_key): 27.0,
            (pickup_key, osapa_key): 26.0,
            (ikorodu_key, dropoff_key): 30.0,
            (ikorodu_key, mile_12_key): 17.0,
            (ikorodu_key, osapa_key): 24.0,
            (mile_12_key, dropoff_key): 13.0,
            (mile_12_key, osapa_key): 21.0,
            (osapa_key, dropoff_key): 6.0,
        }

        def route_distance_side_effect(origin, destination):
            return route_distances.get(
                (point_key(origin), point_key(destination)), 999.0
            )

        def directions_side_effect(origin, points):
            if len(points) == 3:
                return [(8.0, 20), (17.0, 42), (13.0, 31)]
            return None

        route_distance_mock.side_effect = route_distance_side_effect
        directions_mock.side_effect = directions_side_effect

        success = generate_relay_legs_sync(order.id)

        self.assertTrue(success)
        order.refresh_from_db()
        legs = list(order.legs.order_by("leg_number"))

        self.assertEqual(order.routing_status, order.RoutingStatus.READY)
        self.assertEqual(len(legs), 3)
        self.assertEqual(legs[0].end_relay_node_id, ikorodu.id)
        self.assertEqual(legs[1].start_relay_node_id, ikorodu.id)
        self.assertEqual(legs[1].end_relay_node_id, mile_12.id)
        self.assertEqual(legs[2].start_relay_node_id, mile_12.id)
        self.assertIsNone(legs[2].end_relay_node)
        self.assertEqual(legs[0].distance_km, 8.0)
        self.assertEqual(legs[1].distance_km, 17.0)
        self.assertEqual(legs[2].distance_km, 13.0)

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks._directions_legs", return_value=None)
    @patch("dispatcher.tasks._nearest_rider_to", return_value=None)
    def test_generate_relay_legs_fails_without_full_20km_hub_chain(
        self, _nearest_rider_mock, _directions_mock, _emit_activity_mock
    ):
        from dispatcher.models import RelayNode
        from dispatcher.tasks import generate_relay_legs_sync

        RelayNode.objects.create(
            name="Only Hub",
            address="10km Hub",
            latitude=0,
            longitude=self._lng_for_km(10),
            is_active=True,
        )
        order = self._create_order(total_km=45)

        success = generate_relay_legs_sync(order.id)

        self.assertFalse(success)
        order.refresh_from_db()
        self.assertEqual(order.routing_status, order.RoutingStatus.FAILED)
        self.assertEqual(order.legs.count(), 0)
        self.assertIn("relay-hub chain", order.routing_error.lower())


class RiderAssignmentTaskTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from dispatcher.models import Rider, RelayNode
        from orders.models import Vehicle

        self.user = User.objects.create_user(
            phone="08011110000",
            email="testuser@example.com",
            password="password",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike-Test",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )

        # Create a hub
        self.hub = RelayNode.objects.create(
            name="Test Hub",
            latitude=6.5,
            longitude=3.3,
            address="Test Hub Address",
            is_active=True,
        )

        # Create a rider near the hub
        self.rider_user = User.objects.create_user(
            phone="08022220000",
            email="rider@example.com",
            password="password",
            usertype="Rider",
        )
        self.rider = Rider.objects.create(
            user=self.rider_user,
            rider_id="R123",
            current_latitude=6.501,
            current_longitude=3.301,
            is_authorized=True,
            hub=self.hub,
        )

    @patch("riders.notifications.notify_rider")
    @patch("riders.views.publish_order_assigned_event")
    @patch("dispatcher.tasks.notify_relay_vertical_leads.delay")
    def test_assign_rider_dynamically(
        self, mock_notify_leads, mock_publish, mock_notify
    ):
        from orders.models import Order, OrderLeg
        from dispatcher.tasks import assign_rider_to_sub_order_task

        # Create a parent order and a sub-order
        parent = Order.objects.create(
            order_number="P100",
            user=self.user,
            vehicle=self.vehicle,
            is_relay_order=True,
            pickup_address="Origin",
            pickup_latitude=6.4,
            pickup_longitude=3.2,
        )
        sub_order = Order.objects.create(
            order_number="S101",
            user=self.user,
            parent_order=parent,
            vehicle=self.vehicle,
            pickup_latitude=6.5,
            pickup_longitude=3.3,
            status="Pending",
            pickup_address="Hub Address",
        )
        leg = OrderLeg.objects.create(
            order=parent, leg_number=2, start_relay_node=self.hub, status="Pending"
        )

        # Run task with rider_id=None
        success = assign_rider_to_sub_order_task(str(sub_order.id), str(leg.id), None)

        self.assertTrue(success)
        sub_order.refresh_from_db()
        leg.refresh_from_db()

        self.assertEqual(sub_order.rider, self.rider)
        self.assertEqual(leg.rider, self.rider)
        self.assertEqual(sub_order.status, "Assigned")
        self.assertEqual(leg.status, OrderLeg.Status.ASSIGNED)


class OrderViewSetListTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from orders.models import Vehicle

        self.user = User.objects.create_user(
            phone="08011110000",
            email="list_test@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike-List",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _create_orders(self, count):
        from orders.models import Order, Delivery

        for i in range(count):
            order = Order.objects.create(
                order_number=f"ORD{1000+i}",
                user=self.user,
                vehicle=self.vehicle,
                pickup_address=f"Pickup {i}",
                sender_name=f"Sender {i}",
                sender_phone=f"080{i:08d}",
                total_amount=Decimal("1000.00"),
                payment_status="Pending",
                status="Pending",
            )
            Delivery.objects.create(
                order=order,
                dropoff_address=f"Dropoff {i}",
                receiver_name=f"Receiver {i}",
                receiver_phone=f"090{i:08d}",
            )

    def test_list_paginated_by_default(self):
        self._create_orders(110)
        res = self.client.get("/api/dispatch/orders/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("results", res.data)
        self.assertEqual(len(res.data["results"]), 100)

    def test_list_all_no_pagination(self):
        self._create_orders(110)
        res = self.client.get("/api/dispatch/orders/?all=true")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("results", res.data)
        self.assertEqual(len(res.data), 110)


class OrderViewSetGenerateRelayRouteTests(TestCase):
    def setUp(self):
        from authentication.models import User
        from orders.models import Delivery, Order, Vehicle

        self.user = User.objects.create_user(
            phone="08022223333",
            email="relay_route_test@example.com",
            password="testpassword",
            usertype="Dispatcher",
            contact_name="Dispatcher",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike-Relay-Route",
            max_weight_kg=10,
            base_price=500,
            base_fare=200,
            rate_per_km=50,
            rate_per_minute=5,
            min_fee=500,
            is_active=True,
        )
        self.order = Order.objects.create(
            order_number="ORD-RELAY-REGEN",
            user=self.user,
            vehicle=self.vehicle,
            is_relay_order=True,
            routing_status=Order.RoutingStatus.READY,
            pickup_address="Pickup",
            pickup_latitude=6.5,
            pickup_longitude=3.3,
            sender_name="Sender",
            sender_phone="08011112222",
            total_amount=Decimal("1000.00"),
            payment_status="Pending",
            status="Pending",
        )
        Delivery.objects.create(
            order=self.order,
            dropoff_address="Dropoff",
            dropoff_latitude=6.6,
            dropoff_longitude=3.4,
            receiver_name="Receiver",
            receiver_phone="08033334444",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("dispatcher.utils.emit_activity")
    @patch("dispatcher.tasks.generate_relay_legs_sync", return_value=True)
    def test_generate_relay_route_always_regenerates_ready_orders(
        self, generate_relay_legs_sync_mock, _emit_activity_mock
    ):
        from orders.models import OrderLeg

        OrderLeg.objects.create(order=self.order, leg_number=1, status="Pending")

        res = self.client.post(
            f"/api/dispatch/orders/{self.order.order_number}/generate-relay-route/"
        )

        self.assertEqual(res.status_code, 200, res.data)
        generate_relay_legs_sync_mock.assert_called_once_with(str(self.order.id))
