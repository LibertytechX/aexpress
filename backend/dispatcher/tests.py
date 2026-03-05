from django.test import TestCase
from unittest.mock import patch
from decimal import Decimal

from rest_framework import serializers
from rest_framework.test import APIClient


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
