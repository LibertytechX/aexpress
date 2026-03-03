from django.test import TestCase
from unittest.mock import patch

from rest_framework import serializers


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
