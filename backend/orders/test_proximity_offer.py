from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
from orders.models import Order, Vehicle
from dispatcher.models import Zone
from riders.models import OrderOffer

User = get_user_model()


class ProximityOfferTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="+2348123456789",
            email="merchant@test.com",
            password="password123",
            usertype="Merchant",
        )
        self.vehicle = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=100,
            base_price=500,
            base_fare=500,
            rate_per_km=50,
            rate_per_minute=5,
            is_active=True,
        )
        # Create zones
        self.zone_a = Zone.objects.create(
            name="Zone A", center_lat=6.6059, center_lng=3.3491, is_active=True
        )
        self.zone_b = Zone.objects.create(
            name="Zone B", center_lat=6.4531, center_lng=3.3958, is_active=True
        )

    @patch("requests.get")
    @patch("django.conf.settings.GOOGLE_MAPS_API_KEY", "fake-key")
    def test_process_order_proximity_task(self, mock_get):
        """Test that the background task geocodes and assigns a zone."""
        # 1. Prepare Geocoding response
        mock_geocoding_resp = MagicMock()
        mock_geocoding_resp.status_code = 200
        mock_geocoding_resp.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 6.5, "lng": 3.3}}}],
        }

        # 2. Prepare Distance Matrix response
        mock_dist_matrix_resp = MagicMock()
        mock_dist_matrix_resp.status_code = 200
        mock_dist_matrix_resp.json.return_value = {
            "status": "OK",
            "rows": [
                {
                    "elements": [
                        {"status": "OK", "distance": {"value": 15000}},  # Zone A
                        {"status": "OK", "distance": {"value": 5000}},  # Zone B
                    ]
                }
            ],
        }

        # Define side effect to return correct response based on URL
        def side_effect(url, **kwargs):
            if "geocode" in url:
                return mock_geocoding_resp
            elif "distancematrix" in url:
                return mock_dist_matrix_resp
            return MagicMock(status_code=404)

        mock_get.side_effect = side_effect

        # Create Order (triggers signal which calls .delay, but we'll call task directly)
        order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="Some Address in Lagos",
            total_amount=Decimal("1000.00"),
            distance_km=Decimal("5.0"),
            duration_minutes=15,
        )

        # Call task directly (simulating Celery worker)
        from .tasks import process_order_proximity

        process_order_proximity(order.id)

        # Refresh from DB to see geocoded coordinates
        order.refresh_from_db()

        # Check geocoding happened
        self.assertEqual(order.pickup_latitude, 6.5)
        self.assertEqual(order.pickup_longitude, 3.3)

        # Check OrderOffer was created with correct zone
        offer = OrderOffer.objects.get(order=order)
        self.assertEqual(offer.zone, self.zone_b)
        self.assertEqual(offer.estimated_earnings, Decimal("200.00"))

    def test_proximity_fallback_to_haversine(self):
        """Test fallback to Haversine distance when Google Maps API key is missing."""
        # Mock settings to have NO API KEY
        with self.settings(GOOGLE_MAPS_API_KEY=""):
            # Create Order with coordinates
            order = Order.objects.create(
                user=self.user,
                vehicle=self.vehicle,
                pickup_address="Address",
                pickup_latitude=6.45,
                pickup_longitude=3.40,  # Closer to Zone B
                total_amount=Decimal("1000.00"),
                distance_km=Decimal("5.0"),
                duration_minutes=15,
            )

            # Call task directly
            from .tasks import process_order_proximity

            process_order_proximity(order.id)

            offer = OrderOffer.objects.get(order=order)
            self.assertEqual(offer.zone, self.zone_b)
            self.assertEqual(offer.estimated_earnings, Decimal("200.00"))
