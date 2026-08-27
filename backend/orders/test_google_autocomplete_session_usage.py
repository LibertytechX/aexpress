from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid
from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import User
from orders.models import GoogleAutoCompleteSessionUsage, GooglePlace
from orders.utils import google_place_autocomplete, google_place_details


@override_settings(GOOGLE_MAPS_API_KEY="test-google-maps-key")
class GoogleAutoCompleteSessionUsageModelTests(APITestCase):
    """Unit tests for GoogleAutoCompleteSessionUsage model logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="merchant_session@test.com",
            password="password123",
            phone="08011223344",
            first_name="Session",
            last_name="Merchant",
        )

    def test_create_session_usage_defaults(self):
        """Test default values on session usage creation."""
        token = str(uuid.uuid4())
        usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token,
            user=self.user,
        )
        self.assertEqual(usage.session_token, token)
        self.assertEqual(usage.user, self.user)
        self.assertEqual(
            usage.status, GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS
        )
        self.assertEqual(usage.price_per_session, Decimal("0.0050"))
        self.assertEqual(usage.request_count, 1)
        self.assertIsNone(usage.place_id)
        self.assertIsNone(usage.resolved_at)
        self.assertIn(token, str(usage))

    def test_mark_resolved(self):
        """Test transitioning session to RESOLVED."""
        token = str(uuid.uuid4())
        usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token,
            user=self.user,
        )
        usage.mark_resolved(place_id="google_place_abc_123")
        usage.refresh_from_db()

        self.assertEqual(usage.status, GoogleAutoCompleteSessionUsage.Status.RESOLVED)
        self.assertEqual(usage.place_id, "google_place_abc_123")
        self.assertIsNotNone(usage.resolved_at)

    def test_mark_expired(self):
        """Test transitioning session to EXPIRED."""
        token = str(uuid.uuid4())
        usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token,
            user=self.user,
        )
        usage.mark_expired()
        usage.refresh_from_db()

        self.assertEqual(usage.status, GoogleAutoCompleteSessionUsage.Status.EXPIRED)

    def test_record_hit_creates_and_increments(self):
        """Test record_hit creates on first call and increments on subsequent calls."""
        token = str(uuid.uuid4())

        # First hit creates record
        usage1 = GoogleAutoCompleteSessionUsage.record_hit(
            session_token=token, user=self.user
        )
        self.assertIsNotNone(usage1)
        self.assertEqual(usage1.request_count, 1)
        self.assertEqual(
            usage1.status, GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS
        )

        # Second hit increments count
        usage2 = GoogleAutoCompleteSessionUsage.record_hit(
            session_token=token, user=self.user
        )
        self.assertEqual(usage2.id, usage1.id)
        self.assertEqual(usage2.request_count, 2)

        # Third hit increments count again
        usage3 = GoogleAutoCompleteSessionUsage.record_hit(
            session_token=token, user=self.user
        )
        self.assertEqual(usage3.request_count, 3)

    def test_record_hit_with_empty_token(self):
        """Test record_hit returns None when session token is empty."""
        result = GoogleAutoCompleteSessionUsage.record_hit(session_token="")
        self.assertIsNone(result)

    def test_expire_stale_sessions(self):
        """Test expiring sessions older than a given threshold."""
        token_old = str(uuid.uuid4())
        token_new = str(uuid.uuid4())
        token_resolved = str(uuid.uuid4())

        old_usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token_old,
            status=GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS,
        )
        # Manually set created_at back by 1 hour
        GoogleAutoCompleteSessionUsage.objects.filter(id=old_usage.id).update(
            created_at=timezone.now() - timedelta(hours=1)
        )

        new_usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token_new,
            status=GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS,
        )

        resolved_usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token_resolved,
            status=GoogleAutoCompleteSessionUsage.Status.RESOLVED,
        )

        expired_count = GoogleAutoCompleteSessionUsage.expire_stale_sessions(
            older_than_minutes=30
        )
        self.assertEqual(expired_count, 1)

        old_usage.refresh_from_db()
        new_usage.refresh_from_db()
        resolved_usage.refresh_from_db()

        self.assertEqual(
            old_usage.status, GoogleAutoCompleteSessionUsage.Status.EXPIRED
        )
        self.assertEqual(
            new_usage.status, GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS
        )
        self.assertEqual(
            resolved_usage.status, GoogleAutoCompleteSessionUsage.Status.RESOLVED
        )


@override_settings(GOOGLE_MAPS_API_KEY="test-google-maps-key")
class GooglePlacesUtilsSessionTrackingTests(APITestCase):
    """Integration tests for Google places utils and session usage tracking."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="utils_session@test.com",
            password="password123",
            phone="08022334455",
            first_name="Utils",
            last_name="Tester",
        )

    @patch("orders.utils.requests.get")
    def test_google_place_autocomplete_tracks_session_usage(self, mock_get):
        """Test autocomplete hits create/update GoogleAutoCompleteSessionUsage."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "OK",
            "predictions": [
                {
                    "place_id": "google_lekki_101",
                    "description": "Lekki Phase 1, Lagos, Nigeria",
                    "structured_formatting": {
                        "main_text": "Lekki Phase 1",
                        "secondary_text": "Lagos, Nigeria",
                    },
                }
            ],
        }
        mock_get.return_value = mock_response

        token = str(uuid.uuid4())
        # First keystroke
        results1 = google_place_autocomplete("Lek", session_token=token, user=self.user)
        self.assertEqual(len(results1), 1)

        usage = GoogleAutoCompleteSessionUsage.objects.get(session_token=token)
        self.assertEqual(usage.request_count, 1)
        self.assertEqual(usage.user, self.user)
        self.assertEqual(
            usage.status, GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS
        )

        # Second keystroke
        results2 = google_place_autocomplete(
            "Lekki", session_token=token, user=self.user
        )
        self.assertEqual(len(results2), 1)

        usage.refresh_from_db()
        self.assertEqual(usage.request_count, 2)

    @patch("orders.utils.requests.get")
    def test_google_place_details_resolves_session_usage(self, mock_get):
        """Test place details resolves in-progress GoogleAutoCompleteSessionUsage."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "OK",
            "result": {
                "formatted_address": "10 Admiralty Way, Lekki, Lagos, Nigeria",
                "geometry": {"location": {"lat": 6.4474, "lng": 3.4723}},
            },
        }
        mock_get.return_value = mock_response

        token = str(uuid.uuid4())
        usage = GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token,
            user=self.user,
            status=GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS,
            request_count=3,
        )

        details = google_place_details(place_id="google_lekki_101", session_token=token)
        self.assertIsNotNone(details)
        self.assertEqual(details["lat"], 6.4474)
        self.assertEqual(details["lng"], 3.4723)

        usage.refresh_from_db()
        self.assertEqual(usage.status, GoogleAutoCompleteSessionUsage.Status.RESOLVED)
        self.assertEqual(usage.place_id, "google_lekki_101")
        self.assertIsNotNone(usage.resolved_at)


@override_settings(GOOGLE_MAPS_API_KEY="test-google-maps-key")
class PlacesViewsGoogleSessionE2ETests(APITestCase):
    """End-to-End API view tests for Google Places autocomplete and details session tracking."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="e2e_places@test.com",
            password="password123",
            phone="08033445566",
            first_name="E2E",
            last_name="Merchant",
        )
        self.client.force_authenticate(user=self.user)

    @patch("orders.utils.requests.get")
    def test_places_autocomplete_and_details_e2e_flow(self, mock_get):
        """Test the entire autocomplete to details lifecycle via API endpoints."""
        token = str(uuid.uuid4())

        # 1. Autocomplete call
        mock_auto_response = MagicMock()
        mock_auto_response.raise_for_status.return_value = None
        mock_auto_response.json.return_value = {
            "status": "OK",
            "predictions": [
                {
                    "place_id": "ChIJb_google_place_id",
                    "description": "Victoria Island, Lagos, Nigeria",
                    "structured_formatting": {
                        "main_text": "Victoria Island",
                        "secondary_text": "Lagos, Nigeria",
                    },
                }
            ],
        }
        mock_get.return_value = mock_auto_response

        auto_url = reverse("orders:places_autocomplete")
        res1 = self.client.get(
            auto_url, {"q": "Victoria Island", "session_token": token}
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["status"], "success")

        usage = GoogleAutoCompleteSessionUsage.objects.get(session_token=token)
        self.assertEqual(usage.request_count, 1)
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.price_per_session, Decimal("0.0050"))
        self.assertEqual(
            usage.status, GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS
        )

        # 2. Place Details call
        mock_details_response = MagicMock()
        mock_details_response.raise_for_status.return_value = None
        mock_details_response.json.return_value = {
            "status": "OK",
            "result": {
                "formatted_address": "Victoria Island, Lagos, Nigeria",
                "geometry": {"location": {"lat": 6.4281, "lng": 3.4219}},
            },
        }
        mock_get.return_value = mock_details_response

        details_url = reverse("orders:places_details")
        res2 = self.client.get(
            details_url,
            {
                "place_id": "google:ChIJb_google_place_id",
                "session_token": token,
            },
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["status"], "success")
        self.assertEqual(res2.data["data"]["lat"], 6.4281)
        self.assertEqual(res2.data["data"]["lng"], 3.4219)

        # 3. Verify session usage status is RESOLVED
        usage.refresh_from_db()
        self.assertEqual(usage.status, GoogleAutoCompleteSessionUsage.Status.RESOLVED)
        self.assertEqual(usage.place_id, "ChIJb_google_place_id")
        self.assertIsNotNone(usage.resolved_at)

        # 4. Verify GooglePlace was recorded in the database
        place_in_db = GooglePlace.objects.filter(
            place_id="ChIJb_google_place_id"
        ).first()
        self.assertIsNotNone(place_in_db)
        self.assertEqual(
            place_in_db.formatted_address, "Victoria Island, Lagos, Nigeria"
        )
        self.assertEqual(float(place_in_db.lat), 6.4281)
        self.assertEqual(float(place_in_db.lng), 3.4219)

    @patch("orders.utils.requests.get")
    def test_places_details_served_from_database_cache_without_external_call(
        self, mock_get
    ):
        """Test that place details are served from GooglePlace DB cache without hitting Google."""
        # Pre-seed place in DB
        GooglePlace.objects.create(
            place_id="cached_lekki_place_999",
            formatted_address="99 Admiralty Way, Lekki, Lagos, Nigeria",
            lat=Decimal("6.4500000"),
            lng=Decimal("3.4800000"),
        )

        token = str(uuid.uuid4())
        GoogleAutoCompleteSessionUsage.objects.create(
            session_token=token,
            user=self.user,
            status=GoogleAutoCompleteSessionUsage.Status.IN_PROGRESS,
        )

        details_url = reverse("orders:places_details")
        response = self.client.get(
            details_url,
            {
                "place_id": "google:cached_lekki_place_999",
                "session_token": token,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(
            response.data["data"]["formatted_address"],
            "99 Admiralty Way, Lekki, Lagos, Nigeria",
        )
        self.assertEqual(response.data["data"]["lat"], 6.45)
        self.assertEqual(response.data["data"]["lng"], 3.48)

        # External HTTP request should NOT have been made
        mock_get.assert_not_called()

        # Session should be marked as RESOLVED
        usage = GoogleAutoCompleteSessionUsage.objects.get(session_token=token)
        self.assertEqual(usage.status, GoogleAutoCompleteSessionUsage.Status.RESOLVED)
        self.assertEqual(usage.place_id, "cached_lekki_place_999")

