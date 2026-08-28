from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from unittest.mock import MagicMock, patch

from orders.utils import geocode_address


@override_settings(
    GOOGLE_MAPS_API_KEY="fake-key",
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "orders-utils-tests",
        }
    },
)
class GeocodeAddressTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch("orders.utils.requests.get")
    def test_geocode_address_caches_successful_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 6.5, "lng": 3.3}}}],
        }
        mock_get.return_value = mock_response

        first = geocode_address("15A Example Street")
        second = geocode_address("15A Example Street")

        self.assertEqual(first, {"lat": 6.5, "lng": 3.3})
        self.assertEqual(second, first)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(
            mock_get.call_args.kwargs["params"]["address"],
            "15A Example Street, Lagos, Nigeria",
        )

    @patch("orders.utils.requests.get")
    def test_geocode_address_normalizes_equivalent_inputs_for_cache(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 6.51, "lng": 3.31}}}],
        }
        mock_get.return_value = mock_response

        first = geocode_address("15A Example Street")
        second = geocode_address("  15a   example street, lagos  ")

        self.assertEqual(first, second)
        self.assertEqual(mock_get.call_count, 1)
