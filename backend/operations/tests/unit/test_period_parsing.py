"""Unit tests for Operations services and helper functions."""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from operations import services


class OperationsPeriodTests(TestCase):
    """Test period parsing utilities in operations service."""

    def test_parse_period_supports_dashboard_periods(self):
        for period in [
            "today",
            "yesterday",
            "this_week",
            "past_7_days",
            "this_month",
            "last_month",
            "this_year",
        ]:
            with self.subTest(period=period):
                start_dt, end_dt = services.parse_period(period)
                self.assertLessEqual(start_dt, end_dt)

    def test_parse_period_supports_this_year(self):
        start_dt, end_dt = services.parse_period("this_year")
        now = timezone.now()

        self.assertEqual(start_dt.date(), now.date().replace(month=1, day=1))
        self.assertEqual(start_dt.hour, 0)
        self.assertEqual(start_dt.minute, 0)
        self.assertLessEqual(end_dt, now)

    def test_parse_period_supports_year_month(self):
        start_dt, end_dt = services.parse_period("2026-05")

        self.assertEqual(start_dt.date().isoformat(), "2026-05-01")
        self.assertEqual(end_dt.date().isoformat(), "2026-05-31")


class OperationsKmIntegrityUnitTests(TestCase):
    """Test KM integrity calculation logic."""

    def test_km_integrity_status_passed(self):
        status = services.km_integrity_status(Decimal("100.00"), Decimal("95.00"))
        self.assertEqual(status, "passed")

    def test_km_integrity_status_failed(self):
        status = services.km_integrity_status(Decimal("100.00"), Decimal("80.00"))
        self.assertEqual(status, "failed")

    def test_km_integrity_status_unavailable(self):
        status = services.km_integrity_status(None, None)
        self.assertEqual(status, "unavailable")
