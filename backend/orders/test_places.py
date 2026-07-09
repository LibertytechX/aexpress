from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import MagicMock, patch
from authentication.models import User
from orders.utils import (
    aws_place_autocomplete,
    aws_place_details,
    aws_reverse_geocode,
    geocode_address,
)


@override_settings(
    AWS_ACCESS_KEY_ID="fake-id",
    AWS_SECRET_ACCESS_KEY="fake-key",
    AWS_S3_REGION_NAME="us-east-1",
    AWS_LOCATION_PLACE_INDEX="aexpress-place-index",
    GOOGLE_MAPS_API_KEY="fake-google-key",
)
class AWSLocationHelpersTests(APITestCase):
    @patch("orders.utils.get_aws_location_client")
    def test_aws_place_autocomplete_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search_place_index_for_suggestions.return_value = {
            "Results": [
                {
                    "Text": "15a Kunle Ogunba St, Lekki, Lagos, NGA",
                    "PlaceId": "fake-place-id-123",
                }
            ]
        }
        mock_get_client.return_value = mock_client

        results = aws_place_autocomplete("Kunle Ogunba")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["place_id"], "fake-place-id-123")
        self.assertEqual(
            results[0]["description"], "15a Kunle Ogunba St, Lekki, Lagos, NGA"
        )
        self.assertEqual(results[0]["structured_formatting"]["main_text"], "15a Kunle Ogunba St")
        self.assertEqual(
            results[0]["structured_formatting"]["secondary_text"],
            "Lekki, Lagos, NGA",
        )

    @patch("orders.utils.get_aws_location_client")
    def test_aws_place_details_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_place.return_value = {
            "Place": {
                "Label": "15a Kunle Ogunba St, Lekki, Lagos, NGA",
                "Geometry": {"Point": [3.456, 6.45]},  # [lng, lat]
            }
        }
        mock_get_client.return_value = mock_client

        details = aws_place_details("fake-place-id-123")
        self.assertIsNotNone(details)
        self.assertEqual(details["formatted_address"], "15a Kunle Ogunba St, Lekki, Lagos, NGA")
        self.assertEqual(details["lat"], 6.45)
        self.assertEqual(details["lng"], 3.456)

    @patch("orders.utils.get_aws_location_client")
    def test_aws_reverse_geocode_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search_place_index_for_position.return_value = {
            "Results": [
                {
                    "Place": {
                        "Label": "Lekki Peninsula, Victoria Island, Lagos, NGA"
                    }
                }
            ]
        }
        mock_get_client.return_value = mock_client

        address = aws_reverse_geocode(6.45, 3.456)
        self.assertEqual(address, "Lekki Peninsula, Victoria Island, Lagos, NGA")


@override_settings(
    AWS_ACCESS_KEY_ID="fake-id",
    AWS_SECRET_ACCESS_KEY="fake-key",
    AWS_S3_REGION_NAME="us-east-1",
    AWS_LOCATION_PLACE_INDEX="aexpress-place-index",
    GOOGLE_MAPS_API_KEY="fake-google-key",
)
class PlacesProxyViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testmerchant@example.com",
            password="testpassword123",
            phone="08012345678",
            first_name="Test",
            last_name="Merchant",
        )
        self.client.force_authenticate(user=self.user)

    @patch("orders.places_views.aws_place_autocomplete")
    def test_places_autocomplete_view(self, mock_autocomplete):
        mock_autocomplete.return_value = [
            {
                "place_id": "fake-id",
                "description": "Lagos, Nigeria",
                "structured_formatting": {"main_text": "Lagos", "secondary_text": "Nigeria"},
            }
        ]

        url = reverse("orders:places_autocomplete")
        response = self.client.get(url, {"q": "Lagos"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["place_id"], "fake-id")

    @patch("orders.places_views.aws_place_details")
    def test_place_details_view(self, mock_details):
        mock_details.return_value = {
            "formatted_address": "Lekki, Lagos",
            "lat": 6.45,
            "lng": 3.45,
        }

        url = reverse("orders:places_details")
        response = self.client.get(url, {"place_id": "fake-id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["lat"], 6.45)

    @patch("orders.places_views.aws_reverse_geocode")
    def test_reverse_geocode_view(self, mock_reverse):
        mock_reverse.return_value = "Lekki, Lagos"

        url = reverse("orders:places_reverse_geocode")
        response = self.client.get(url, {"lat": "6.45", "lng": "3.45"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["address"], "Lekki, Lagos")


@override_settings(
    AWS_ACCESS_KEY_ID="fake-id",
    AWS_SECRET_ACCESS_KEY="fake-key",
    AWS_S3_REGION_NAME="us-east-1",
    AWS_LOCATION_PLACE_INDEX="aexpress-place-index",
    GOOGLE_MAPS_API_KEY="fake-google-key",
)
class GeocodeFallbackTests(APITestCase):
    @patch("orders.utils.requests.get")
    @patch("orders.utils.aws_geocode_address")
    def test_geocode_address_google_fails_falls_back_to_aws(
        self, mock_aws_geocode, mock_http_get
    ):
        # Mock Google Maps failure (returns REQUEST_DENIED status)
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "REQUEST_DENIED", "results": []}
        mock_http_get.return_value = mock_response

        # Mock AWS Geocoding success
        mock_aws_geocode.return_value = {"lat": 6.4, "lng": 3.4}

        res = geocode_address("Some query that fails in Google")
        self.assertEqual(res, {"lat": 6.4, "lng": 3.4})
        self.assertEqual(mock_aws_geocode.call_count, 1)

    @patch("orders.utils.requests.get")
    @patch("orders.utils.aws_geocode_address")
    def test_geocode_address_google_exception_falls_back_to_aws(
        self, mock_aws_geocode, mock_http_get
    ):
        # Mock Google Maps raising exception (e.g. timeout)
        mock_http_get.side_effect = Exception("Timeout")

        # Mock AWS Geocoding success
        mock_aws_geocode.return_value = {"lat": 6.4, "lng": 3.4}

        res = geocode_address("Some query that times out")
        self.assertEqual(res, {"lat": 6.4, "lng": 3.4})
        self.assertEqual(mock_aws_geocode.call_count, 1)
