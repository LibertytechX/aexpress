from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from authentication.models import User
from orders.models import Vehicle, MerchantPricingOverride
from orders.pricing import calculate_effective_fare


class MerchantPricingOverrideTests(TestCase):
    """Tests for calculate_effective_fare with merchant overrides."""

    def setUp(self):
        self.merchant = User.objects.create_user(
            phone="08011110001",
            email="testmerchant@example.com",
            password="testpass",
            usertype="Merchant",
            business_name="Test Merchant",
        )
        self.vehicle = Vehicle.objects.create(
            name="TestBike",
            max_weight_kg=20,
            base_price=Decimal("0.00"),
            base_fare=Decimal("0.00"),
            rate_per_km=Decimal("0.00"),
            rate_per_minute=Decimal("0.00"),
            min_distance_km=Decimal("0.00"),
            min_fee=Decimal("0.00"),
            pricing_tiers={
                "type": "tiered",
                "floor_km": 6,
                "floor_fee": 1700,
                "tiers": [
                    {"max_km": 10, "rate": 275},
                    {"max_km": 15, "rate": 235},
                    {"max_km": 25, "rate": 200},
                    {"rate": 200},
                ],
            },
        )

    # ── 1. No override → global vehicle pricing ──────────────────────
    def test_no_override_falls_back_to_vehicle(self):
        fare = calculate_effective_fare(self.merchant, self.vehicle, 10, 0)
        self.assertEqual(fare, Decimal("2750.00"))

    def test_no_merchant_falls_back_to_vehicle(self):
        fare = calculate_effective_fare(None, self.vehicle, 10, 0)
        self.assertEqual(fare, Decimal("2750.00"))

    # ── 2. Flat fee override ─────────────────────────────────────────
    def test_flat_fee_overrides_everything(self):
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            flat_fee=Decimal("5000.00"),
            is_active=True,
        )
        fare = calculate_effective_fare(self.merchant, self.vehicle, 50, 120)
        self.assertEqual(fare, Decimal("5000.00"))

    def test_flat_fee_zero_is_valid(self):
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            flat_fee=Decimal("0.00"),
            is_active=True,
        )
        fare = calculate_effective_fare(self.merchant, self.vehicle, 10, 30)
        self.assertEqual(fare, Decimal("0.00"))

    # ── 3. Merchant tiered override ──────────────────────────────────
    def test_merchant_tiers_override_global(self):
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            pricing_tiers={
                "type": "tiered",
                "floor_km": 5,
                "floor_fee": 1000,
                "tiers": [
                    {"max_km": 10, "rate": 150},
                    {"rate": 100},
                ],
            },
            is_active=True,
        )
        # 3 km → floor fee
        self.assertEqual(
            calculate_effective_fare(self.merchant, self.vehicle, 3, 0),
            Decimal("1000.00"),
        )
        # 8 km → 8 * 150 = 1200
        self.assertEqual(
            calculate_effective_fare(self.merchant, self.vehicle, 8, 0),
            Decimal("1200.00"),
        )
        # 15 km → 15 * 100 = 1500
        self.assertEqual(
            calculate_effective_fare(self.merchant, self.vehicle, 15, 0),
            Decimal("1500.00"),
        )

    # ── 4. Flat fee takes precedence over tiers ──────────────────────
    def test_flat_fee_beats_tiers(self):
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            flat_fee=Decimal("2500.00"),
            pricing_tiers={
                "type": "tiered",
                "floor_km": 5,
                "floor_fee": 1000,
                "tiers": [{"rate": 150}],
            },
            is_active=True,
        )
        fare = calculate_effective_fare(self.merchant, self.vehicle, 20, 0)
        self.assertEqual(fare, Decimal("2500.00"))

    # ── 5. Inactive override is ignored ──────────────────────────────
    def test_inactive_override_ignored(self):
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            flat_fee=Decimal("999.00"),
            is_active=False,
        )
        fare = calculate_effective_fare(self.merchant, self.vehicle, 10, 0)
        # Should fall back to global: 10 * 275 = 2750
        self.assertEqual(fare, Decimal("2750.00"))

    # ── 6. Override is per-vehicle ────────────────────────────────────
    def test_override_is_per_vehicle(self):
        other_vehicle = Vehicle.objects.create(
            name="TestVan",
            max_weight_kg=500,
            base_price=Decimal("0.00"),
            base_fare=Decimal("500.00"),
            rate_per_km=Decimal("100.00"),
            rate_per_minute=Decimal("0.00"),
            min_distance_km=Decimal("0.00"),
            min_fee=Decimal("500.00"),
        )
        MerchantPricingOverride.objects.create(
            merchant=self.merchant,
            vehicle=self.vehicle,
            flat_fee=Decimal("3000.00"),
            is_active=True,
        )
        # Bike override → flat 3000
        self.assertEqual(
            calculate_effective_fare(self.merchant, self.vehicle, 10, 0),
            Decimal("3000.00"),
        )
        # Van → no override → global legacy: max(500 + 10*100 + 0, 500) = 1500
        van_fare = calculate_effective_fare(self.merchant, other_vehicle, 10, 0)
        self.assertEqual(van_fare, Decimal("1500.00"))

