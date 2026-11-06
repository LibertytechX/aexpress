from decimal import Decimal

from django.test import TestCase

from orders.models import Vehicle


class VehicleTieredPricingTests(TestCase):
    def _make_vehicle(self, pricing_tiers):
        return Vehicle.objects.create(
            name=f"Test Vehicle {Vehicle.objects.count() + 1}",
            max_weight_kg=100,
            base_price=Decimal("0.00"),
            base_fare=Decimal("0.00"),
            rate_per_km=Decimal("0.00"),
            rate_per_minute=Decimal("0.00"),
            min_distance_km=Decimal("0.00"),
            min_fee=Decimal("0.00"),
            pricing_tiers=pricing_tiers,
        )

    def test_calculate_fare_supports_four_tiers_with_25km_breakpoint(self):
        vehicle = self._make_vehicle(
            {
                "type": "tiered",
                "floor_km": 6,
                "floor_fee": 1700,
                "tiers": [
                    {"max_km": 10, "rate": 275},
                    {"max_km": 15, "rate": 235},
                    {"max_km": 25, "rate": 200},
                    {"rate": 200},
                ],
            }
        )

        self.assertEqual(vehicle.calculate_fare(5, 0), Decimal("1700.00"))
        self.assertEqual(vehicle.calculate_fare(7, 0), Decimal("1925.00"))
        self.assertEqual(vehicle.calculate_fare(12, 0), Decimal("2820.00"))
        self.assertEqual(vehicle.calculate_fare(15, 0), Decimal("3525.00"))
        self.assertEqual(vehicle.calculate_fare(20, 0), Decimal("4000.00"))
        self.assertEqual(vehicle.calculate_fare(25, 0), Decimal("5000.00"))
        self.assertEqual(vehicle.calculate_fare(26, 0), Decimal("5200.00"))
        self.assertEqual(vehicle.calculate_fare(30, 0), Decimal("6000.00"))

    def test_calculate_fare_backwards_compatible_three_tiers_last_unbounded(self):
        vehicle = self._make_vehicle(
            {
                "type": "tiered",
                "floor_km": 6,
                "floor_fee": 1700,
                "tiers": [
                    {"max_km": 10, "rate": 275},
                    {"max_km": 15, "rate": 235},
                    {"rate": 200},
                ],
            }
        )

        self.assertEqual(vehicle.calculate_fare(5, 0), Decimal("1700.00"))
        self.assertEqual(vehicle.calculate_fare(7, 0), Decimal("1925.00"))
        self.assertEqual(vehicle.calculate_fare(12, 0), Decimal("2820.00"))
        self.assertEqual(vehicle.calculate_fare(20, 0), Decimal("4000.00"))
        self.assertEqual(vehicle.calculate_fare(30, 0), Decimal("6000.00"))
