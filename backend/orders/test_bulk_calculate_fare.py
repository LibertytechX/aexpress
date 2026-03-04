from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from authentication.models import User
from orders.models import Vehicle


class BulkCalculateFareViewTests(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email="testmerchant@example.com",
            password="testpassword123",
            phone="08012345678",
            first_name="Test",
            last_name="Merchant",
        )
        self.client.force_authenticate(user=self.user)

        # Create vehicles
        self.bike = Vehicle.objects.create(
            name="Bike",
            max_weight_kg=10,
            base_price=500.0,
            base_fare=500.0,
            rate_per_km=100.0,
            rate_per_minute=20.0,
            min_fee=600.0,
            is_active=True,
        )

        # Test tired pricing scheme vehicle
        self.tiered_vehicle = Vehicle.objects.create(
            name="TieredVan",
            max_weight_kg=100,
            base_price=1000.0,
            base_fare=1000.0,
            rate_per_km=0.0,
            rate_per_minute=0.0,
            min_fee=1000.0,
            is_active=True,
            pricing_tiers={
                "type": "tiered",
                "floor_km": 5,
                "floor_fee": 1500,
                "tiers": [{"max_km": 10, "rate": 300}, {"max_km": 20, "rate": 250}],
            },
        )

        self.url = reverse("orders:bulk_calculate_fare")

    def test_missing_fields(self):
        response = self.client.post(self.url, {"mode": "quick"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data["error"])

    @patch("orders.views.calculate_route")
    def test_quick_send_mode(self, mock_calculate_route):
        # Mock Google Maps calculation response
        mock_calculate_route.return_value = {
            "distance_km": 10.0,
            "duration_minutes": 30,
        }

        payload = {
            "mode": "quick",
            "pickup": {"lat": 6.5244, "long": 3.3792},
            "deliveries": [{"lat": 6.6018, "long": 3.3515}],
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertTrue(data["success"])
        self.assertEqual(data["mode"], "quick")

        # Check Bike calculation (Base:500 + Dist:1000 + Time:600 = 2100)
        self.assertIn("Bike", data["vehicles"])
        self.assertEqual(data["vehicles"]["Bike"]["price"], 2100.0)

        # Check TieredVan calculation [tiered, floor 1500, dist 10 -> rate 300] = 3000
        self.assertIn("TieredVan", data["vehicles"])
        self.assertEqual(data["vehicles"]["TieredVan"]["price"], 3000.0)

    @patch("orders.views.calculate_route")
    def test_multi_drop_mode(self, mock_calculate_route):
        # Return different routes depending on if it's the first or second call
        def mock_route_calculator(origin, destinations):
            if "first" in destinations[0]:  # mock distinguishing factor
                return {"distance_km": 4.0, "duration_minutes": 15}
            else:
                return {"distance_km": 15.0, "duration_minutes": 45}

        mock_calculate_route.side_effect = mock_route_calculator

        payload = {
            "mode": "multi",
            "pickup": {"lat": 6.0, "long": 3.0},
            "deliveries": [
                {"lat": 6.1, "long": 3.1, "first": True},
                {"lat": 6.2, "long": 3.2, "second": True},
            ],
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["mode"], "multi")

        # Drop 1 (Bike): 500 + 4*100 + 15*20 = 1200
        # Drop 2 (Bike): 500 + 15*100 + 45*20 = 2900
        # Bike Total = 4100
        self.assertEqual(float(data["vehicles"]["Bike"]["price"]), 4100.0)
        self.assertEqual(float(data["vehicles"]["Bike"]["distance_km"]), 19.0)  # 4 + 15

        # Drop 1 (TieredVan): 4 <= floor(5) -> 1500
        # Drop 2 (TieredVan): 15 <= tier 1(20) -> 15*250 = 3750
        # TieredVan total = 5250
        self.assertEqual(float(data["vehicles"]["TieredVan"]["price"]), 5250.0)

    @patch("orders.views.calculate_route")
    def test_route_calculation_failure(self, mock_calculate_route):
        # Simulate Google API failure
        mock_calculate_route.return_value = None

        payload = {
            "mode": "quick",
            "pickup": {"lat": 6.0, "long": 3.0},
            "deliveries": [{"lat": 6.1, "long": 3.1}],
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
