from unittest.mock import patch, MagicMock
from django.test import TestCase
from authentication.models import User
from dispatcher.models import Rider
from riders.models import RiderDocument, RiderFaceMatchLog, RiderSession
from riders.serializers import RiderFaceMatchRequestSerializer
from riders.tasks import process_rider_facematch_task
from sparky_utils.exceptions import ServiceException


class RiderFaceMatchSerializerTests(TestCase):
    def test_valid_image_url(self):
        data = {"image_url": "https://storage.aexpress.com/selfies/rider_123.jpg"}
        serializer = RiderFaceMatchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["image_url"], data["image_url"])

    def test_missing_image_url(self):
        serializer = RiderFaceMatchRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("image_url", serializer.errors)

    def test_invalid_image_url(self):
        serializer = RiderFaceMatchRequestSerializer(data={"image_url": "not-a-valid-url"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("image_url", serializer.errors)


class RiderFaceMatchTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="08011223344",
            email="rider.facematch@example.com",
            password="securepassword123",
            first_name="Test",
            last_name="Rider",
            contact_name="Test Rider",
            usertype="Rider",
        )
        self.rider = Rider.objects.create(
            user=self.user,
            rider_id="RD9999",
            is_independent_rider=True,
            is_authorized=True,
            status=Rider.Status.ONLINE,
        )
        self.profile_doc = RiderDocument.objects.create(
            rider=self.rider,
            doc_type=RiderDocument.DocType.PROFILE_PHOTO,
            file_url="https://storage.aexpress.com/docs/profile.jpg",
            status=RiderDocument.Status.APPROVED,
        )
        self.session = RiderSession.objects.create(
            rider=self.rider,
            refresh_token="mock_refresh_token_12345",
            is_active=True,
            expires_at="2030-01-01T00:00:00Z",
        )

    @patch("riders.tasks._publish_to_ably_channel")
    @patch("requests.post")
    @patch("requests.get")
    def test_task_success_match(self, mock_get, mock_post, mock_publish):
        # Mock image downloads
        mock_resp_img = MagicMock()
        mock_resp_img.content = b"fake_image_bytes"
        mock_resp_img.raise_for_status.return_value = None
        mock_get.return_value = mock_resp_img

        # Mock KYC CompareFacesView response (Success match)
        mock_kyc_resp = MagicMock()
        mock_kyc_resp.status_code = 200
        mock_kyc_resp.json.return_value = {
            "status": "success",
            "message": "Data Processed Successfully",
            "data": {
                "data": {
                    "result": True,
                    "similarity": 96.5,
                },
                "extra_data": {
                    "Result": "Same person",
                    "Similarity": "96.5",
                },
            },
        }
        mock_post.return_value = mock_kyc_resp

        log = RiderFaceMatchLog.objects.create(
            rider=self.rider,
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            reference_photo_url=self.profile_doc.file_url,
            status=RiderFaceMatchLog.Status.PENDING,
        )

        process_rider_facematch_task(
            rider_id=str(self.rider.id),
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            channel_name="facematch:RD9999",
            log_id=str(log.id),
        )

        # Refresh log and rider
        log.refresh_from_db()
        self.rider.refresh_from_db()
        self.session.refresh_from_db()

        self.assertEqual(log.status, RiderFaceMatchLog.Status.SUCCESS)
        self.assertTrue(log.is_match)
        self.assertEqual(log.similarity, 96.5)

        # Rider remains authorized
        self.assertTrue(self.rider.is_authorized)
        self.assertTrue(self.session.is_active)

        # Ably event published
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        channel, event, payload = args
        self.assertEqual(channel, "facematch:RD9999")
        self.assertEqual(event, "facematch_result")
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["matched"])

    @patch("riders.tasks._publish_to_ably_channel")
    @patch("requests.post")
    @patch("requests.get")
    def test_task_failed_match_deauthorizes_rider(self, mock_get, mock_post, mock_publish):
        mock_resp_img = MagicMock()
        mock_resp_img.content = b"fake_image_bytes"
        mock_resp_img.raise_for_status.return_value = None
        mock_get.return_value = mock_resp_img

        # Mock KYC CompareFacesView response (Failed match)
        mock_kyc_resp = MagicMock()
        mock_kyc_resp.status_code = 200
        mock_kyc_resp.json.return_value = {
            "status": "success",
            "message": "Data Processed Successfully",
            "data": {
                "data": {
                    "result": False,
                    "similarity": 22.0,
                },
                "extra_data": {
                    "Result": "Different person",
                    "Similarity": "22.0",
                },
            },
        }
        mock_post.return_value = mock_kyc_resp

        log = RiderFaceMatchLog.objects.create(
            rider=self.rider,
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            reference_photo_url=self.profile_doc.file_url,
            status=RiderFaceMatchLog.Status.PENDING,
        )

        process_rider_facematch_task(
            rider_id=str(self.rider.id),
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            channel_name="facematch:RD9999",
            log_id=str(log.id),
        )

        log.refresh_from_db()
        self.rider.refresh_from_db()
        self.session.refresh_from_db()

        self.assertEqual(log.status, RiderFaceMatchLog.Status.FAILED)
        self.assertFalse(log.is_match)
        self.assertEqual(log.similarity, 22.0)

        # Rider MUST be blocked / unauthorized and offline
        self.assertFalse(self.rider.is_authorized)
        self.assertEqual(self.rider.status, Rider.Status.OFFLINE)

        # Active session must be deactivated
        self.assertFalse(self.session.is_active)

        # Ably event published with logout action
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        channel, event, payload = args
        self.assertEqual(channel, "facematch:RD9999")
        self.assertEqual(event, "facematch_result")
        self.assertEqual(payload["status"], "failed")
        self.assertFalse(payload["matched"])
        self.assertEqual(payload["action"], "logout")

    @patch("riders.tasks._publish_to_ably_channel")
    @patch("requests.get")
    def test_task_image_download_failure(self, mock_get, mock_publish):
        mock_get.side_effect = Exception("Connection timeout while downloading selfie")

        log = RiderFaceMatchLog.objects.create(
            rider=self.rider,
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            reference_photo_url=self.profile_doc.file_url,
            status=RiderFaceMatchLog.Status.PENDING,
        )

        process_rider_facematch_task(
            rider_id=str(self.rider.id),
            selfie_url="https://storage.aexpress.com/selfies/selfie.jpg",
            channel_name="facematch:RD9999",
            log_id=str(log.id),
        )

        log.refresh_from_db()
        self.assertEqual(log.status, RiderFaceMatchLog.Status.ERROR)
        self.assertIn("Connection timeout", log.error_message)

        # Error notification sent to Ably
        mock_publish.assert_called_once()
        channel, event, payload = mock_publish.call_args[0]
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["matched"])

