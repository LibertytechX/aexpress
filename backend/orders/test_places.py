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
    geoapify_place_autocomplete,
    geoapify_place_details,
    geoapify_geocode_address,
    geoapify_reverse_geocode,
    mapbox_place_autocomplete,
    mapbox_place_details,
    mapbox_reverse_geocode,
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
        self.assertEqual(response.data["data"][0]["place_id"], "aws:fake-id")

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

    @patch("orders.places_views.aws_geocode_address")
    def test_geocode_view(self, mock_geocode):
        mock_geocode.return_value = {"lat": 6.5, "lng": 3.3}

        url = reverse("orders:places_geocode")
        response = self.client.get(url, {"address": "Ojota"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["lat"], 6.5)
        self.assertEqual(response.data["data"]["lng"], 3.3)

        # Mock geocode failure
        mock_geocode.return_value = None
        response = self.client.get(url, {"address": "InvalidPlaceName"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Missing query parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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


@override_settings(GEOAPIFY_API_KEY="test-geoapify-key")
class GeoapifyTests(APITestCase):
    @patch("orders.utils.requests.get")
    def test_geoapify_place_autocomplete(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {
                    "place_id": "test_place_123",
                    "formatted": "Lekki Phase 1, Lagos, Nigeria",
                    "lat": 6.43,
                    "lon": 3.48
                }
            ]
        }
        mock_get.return_value = mock_response

        res = geoapify_place_autocomplete("Lekki")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["place_id"], "geoapify:test_place_123")
        self.assertEqual(res[0]["description"], "Lekki Phase 1, Lagos, Nigeria")
        self.assertEqual(res[0]["lat"], 6.43)
        self.assertEqual(res[0]["lng"], 3.48)
        self.assertEqual(res[0]["structured_formatting"]["main_text"], "Lekki Phase 1")

    @patch("orders.utils.requests.get")
    def test_geoapify_place_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "formatted": "Lekki Phase 1, Lagos, Nigeria",
                        "lat": 6.43,
                        "lon": 3.48
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        res = geoapify_place_details("test_place_123")
        self.assertIsNotNone(res)
        self.assertEqual(res["formatted_address"], "Lekki Phase 1, Lagos, Nigeria")
        self.assertEqual(res["lat"], 6.43)
        self.assertEqual(res["lng"], 3.48)

    @patch("orders.utils.requests.get")
    def test_geoapify_geocode_address(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {
                    "lat": 6.43,
                    "lon": 3.48
                }
            ]
        }
        mock_get.return_value = mock_response

        res = geoapify_geocode_address("Lekki Phase 1")
        self.assertIsNotNone(res)
        self.assertEqual(res["lat"], 6.43)
        self.assertEqual(res["lng"], 3.48)

    @patch("orders.utils.requests.get")
    def test_geoapify_reverse_geocode(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {
                    "formatted": "Lekki Phase 1, Lagos, Nigeria"
                }
            ]
        }
        mock_get.return_value = mock_response

        res = geoapify_reverse_geocode(6.43, 3.48)
        self.assertEqual(res, "Lekki Phase 1, Lagos, Nigeria")


@override_settings(GEOAPIFY_API_KEY="test-geoapify-key")
class PlacesProxyViewsGeoapifyTests(APITestCase):
    def setUp(self):
        self.merchant = User.objects.create_user(
            email="merchant_geo@test.com",
            password="password123",
            phone="08098765432",
            first_name="Geo",
            last_name="Apify",
        )
        self.client.force_authenticate(user=self.merchant)

    @patch("orders.places_views.geoapify_place_autocomplete")
    def test_autocomplete_geoapify_success(self, mock_autocomplete):
        mock_autocomplete.return_value = [
            {
                "place_id": "geoapify:test_123",
                "description": "Lekki",
                "is_geoapify": True,
                "lat": 6.4,
                "lng": 3.4,
                "structured_formatting": {
                    "main_text": "Lekki",
                    "secondary_text": "Lagos"
                }
            }
        ]
        url = reverse("orders:places_autocomplete")
        response = self.client.get(url, {"q": "Lekki"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["place_id"], "geoapify:test_123")

    @patch("orders.places_views.geoapify_place_details")
    def test_details_geoapify_success(self, mock_details):
        mock_details.return_value = {
            "formatted_address": "Lekki",
            "lat": 6.4,
            "lng": 3.4
        }
        url = reverse("orders:places_details")
        response = self.client.get(url, {"place_id": "geoapify:test_123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["lat"], 6.4)

    @patch("orders.places_views.geoapify_reverse_geocode")
    def test_reverse_geocode_geoapify_success(self, mock_rev):
        mock_rev.return_value = "Lekki"
        url = reverse("orders:places_reverse_geocode")
        response = self.client.get(url, {"lat": "6.4", "lng": "3.4"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["address"], "Lekki")

    @patch("orders.places_views.geoapify_geocode_address")
    def test_geocode_geoapify_success(self, mock_geocode):
        mock_geocode.return_value = {"lat": 6.4, "lng": 3.4}
        url = reverse("orders:places_geocode")
        response = self.client.get(url, {"address": "Lekki"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["lat"], 6.4)


@override_settings(MAPBOX_ACCESS_TOKEN="test-mapbox-token")
class MapboxTests(APITestCase):
    @patch("orders.utils.requests.get")
    def test_mapbox_reverse_geocode_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "full_address": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria"
                    }
                }
            ],
        }
        mock_get.return_value = mock_response

        address = mapbox_reverse_geocode(6.45, 3.456)

        self.assertEqual(address, "15a Kunle Ogunba St, Lekki, Lagos, Nigeria")
        mock_get.assert_called_once_with(
            "https://api.mapbox.com/search/geocode/v6/reverse",
            params={
                "longitude": 3.456,
                "latitude": 6.45,
                "access_token": "test-mapbox-token",
            },
            timeout=5,
        )

    @patch("orders.utils.requests.get")
    def test_mapbox_place_autocomplete_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "mapbox_123",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [3.456, 6.45]
                    },
                    "properties": {
                        "mapbox_id": "mapbox_123",
                        "name": "Kunle Ogunba St",
                        "place_formatted": "Lekki, Lagos, Nigeria",
                        "full_address": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        res = mapbox_place_autocomplete("Kunle Ogunba")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["place_id"], "mapbox:mapbox_123")
        self.assertEqual(res[0]["description"], "15a Kunle Ogunba St, Lekki, Lagos, Nigeria")
        self.assertEqual(res[0]["structured_formatting"]["main_text"], "Kunle Ogunba St")
        self.assertEqual(res[0]["structured_formatting"]["secondary_text"], "Lekki, Lagos, Nigeria")
        self.assertTrue(res[0]["is_mapbox"])
        self.assertEqual(res[0]["lat"], 6.45)
        self.assertEqual(res[0]["lng"], 3.456)

    @patch("orders.utils.requests.get")
    def test_mapbox_place_autocomplete_with_coordinates(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "mapbox_123",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [3.456, 6.45]
                    },
                    "properties": {
                        "mapbox_id": "mapbox_123",
                        "name": "Kunle Ogunba St",
                        "place_formatted": "Lekki, Lagos, Nigeria",
                        "full_address": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        res = mapbox_place_autocomplete("Kunle Ogunba")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["place_id"], "mapbox:mapbox_123")
        self.assertEqual(res[0]["lat"], 6.45)
        self.assertEqual(res[0]["lng"], 3.456)


    @patch("orders.utils.requests.get")
    def test_mapbox_place_details_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [3.456, 6.45]  # [lng, lat]
                    },
                    "properties": {
                        "name": "Kunle Ogunba St",
                        "full_address": "15a Kunle Ogunba St, Lekki, Lagos, Nigeria"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        res = mapbox_place_details("mapbox_123")
        self.assertIsNotNone(res)
        self.assertEqual(res["formatted_address"], "15a Kunle Ogunba St, Lekki, Lagos, Nigeria")
        self.assertEqual(res["lat"], 6.45)
        self.assertEqual(res["lng"], 3.456)


@override_settings(GEOAPIFY_API_KEY="test-geoapify-key", MAPBOX_ACCESS_TOKEN="test-mapbox-token")
class PlacesProxyViewsMapboxTests(APITestCase):
    def setUp(self):
        self.merchant = User.objects.create_user(
            email="merchant_mapbox@test.com",
            password="password123",
            phone="08098765433",
            first_name="Map",
            last_name="Box",
        )
        self.client.force_authenticate(user=self.merchant)

    @patch("orders.places_views.geoapify_place_autocomplete")
    @patch("orders.places_views.mapbox_place_autocomplete")
    def test_autocomplete_fallback_to_mapbox(self, mock_mapbox, mock_geoapify):
        mock_geoapify.return_value = []
        mock_mapbox.return_value = [
            {
                "place_id": "mapbox:test_123",
                "description": "Lekki, Lagos",
                "is_mapbox": True,
                "structured_formatting": {
                    "main_text": "Lekki",
                    "secondary_text": "Lagos"
                }
            }
        ]

        url = reverse("orders:places_autocomplete")
        response = self.client.get(url, {"q": "Lekki"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["place_id"], "mapbox:test_123")
        mock_geoapify.assert_called_once()
        mock_mapbox.assert_called_once()

    @patch("orders.places_views.aws_reverse_geocode")
    @patch("orders.places_views.mapbox_reverse_geocode")
    @patch("orders.places_views.geoapify_reverse_geocode")
    def test_reverse_geocode_fallback_to_mapbox(
        self, mock_geoapify, mock_mapbox, mock_aws
    ):
        mock_geoapify.return_value = None
        mock_mapbox.return_value = "Lekki, Lagos"

        url = reverse("orders:places_reverse_geocode")
        response = self.client.get(url, {"lat": "6.4", "lng": "3.4"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["address"], "Lekki, Lagos")
        mock_geoapify.assert_called_once_with(6.4, 3.4)
        mock_mapbox.assert_called_once_with(6.4, 3.4)
        mock_aws.assert_not_called()

    @patch("orders.places_views.mapbox_place_details")
    def test_details_mapbox_success(self, mock_details):
        mock_details.return_value = {
            "formatted_address": "Lekki, Lagos",
            "lat": 6.4,
            "lng": 3.4
        }
        url = reverse("orders:places_details")
        response = self.client.get(url, {"place_id": "mapbox:test_123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["lat"], 6.4)
        mock_details.assert_called_once_with("test_123", session_token="")
