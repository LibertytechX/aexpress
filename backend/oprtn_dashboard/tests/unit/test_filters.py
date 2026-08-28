"""Unit tests for Operations Dashboard filters and parsers."""

from types import SimpleNamespace
from django.test import TestCase
from oprtn_dashboard.filters import parse_filter


class DashboardFiltersUnitTest(TestCase):
    """Unit tests for parse_filter function."""

    def test_parse_filter_default_fallback(self):
        req = SimpleNamespace(query_params={})
        start, end, descriptor = parse_filter(req)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertLessEqual(start, end)
        self.assertIn("filter", descriptor)

    def test_parse_filter_annual(self):
        req = SimpleNamespace(query_params={"filter": "annually"})
        start, end, descriptor = parse_filter(req)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertEqual(descriptor["filter"], "annually")
