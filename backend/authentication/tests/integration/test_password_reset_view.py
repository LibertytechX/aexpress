"""Integration tests for RequestPasswordResetView endpoint."""

from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from authentication.models import User


class RequestPasswordResetViewIntegrationTest(TestCase):
    """Integration test suite for RequestPasswordResetView."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("authentication:request_password_reset")
        self.user = User.objects.create_user(
            email="reset_integration@example.com",
            phone="+2348099887766",
            password="StrongPassword123!",
            contact_name="Integration Reset User",
            business_name="Integration Logistics",
        )

    @patch("authentication.views.send_password_reset_otp_task.delay")
    def test_request_reset_with_email_queues_celery_task(self, mock_task_delay):
        """Requesting password reset with email queues Celery task with user ID."""
        response = self.client.post(self.url, {"email": self.user.email}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("password reset code shortly", response.data["message"])

        mock_task_delay.assert_called_once_with(str(self.user.id))

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)
        self.assertIsNotNone(self.user.password_reset_token_created)

    @patch("authentication.views.send_password_reset_otp_task.delay")
    def test_request_reset_with_phone_queues_celery_task(self, mock_task_delay):
        """Requesting password reset with phone_number queues Celery task with user ID."""
        response = self.client.post(
            self.url, {"phone_number": self.user.phone}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        mock_task_delay.assert_called_once_with(str(self.user.id))

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)

    @patch("authentication.views.send_password_reset_otp_task.delay")
    def test_request_reset_nonexistent_user_prevents_enumeration(self, mock_task_delay):
        """Nonexistent email returns 200 without queueing Celery task."""
        response = self.client.post(
            self.url, {"email": "doesnotexist@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_task_delay.assert_not_called()

    def test_request_reset_missing_both_email_and_phone_returns_400(self):
        """Empty request body returns 400 Bad Request."""
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])


class MobileRequestPasswordResetViewIntegrationTest(TestCase):
    """Integration test suite for MobileRequestPasswordResetView."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("authentication:mobile_request_password_reset")
        self.user = User.objects.create_user(
            email="mobile_reset@example.com",
            phone="+2348033445566",
            password="StrongPassword123!",
            contact_name="Mobile Reset User",
            business_name="Mobile Logistics",
        )

    @patch("authentication.views.send_mobile_password_reset_otp_task.delay")
    def test_mobile_request_reset_with_email_queues_celery_task(
        self, mock_task_delay
    ):
        """Requesting mobile reset with email queues send_mobile_password_reset_otp_task."""
        response = self.client.post(
            self.url, {"email": self.user.email}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_task_delay.assert_called_once_with(str(self.user.id))

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)

    @patch("authentication.views.send_mobile_password_reset_otp_task.delay")
    def test_mobile_request_reset_with_phone_queues_celery_task(
        self, mock_task_delay
    ):
        """Requesting mobile reset with phone queues send_mobile_password_reset_otp_task."""
        response = self.client.post(
            self.url, {"phone": self.user.phone}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_task_delay.assert_called_once_with(str(self.user.id))

    @patch("authentication.views.send_mobile_password_reset_otp_task.delay")
    def test_mobile_request_reset_nonexistent_user_prevents_enumeration(
        self, mock_task_delay
    ):
        """Nonexistent email returns 200 without queueing Celery task."""
        response = self.client.post(
            self.url, {"email": "doesnotexist@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_task_delay.assert_not_called()

    def test_mobile_request_reset_missing_identifier_returns_400(self):
        """Missing both email and phone returns 400 Bad Request."""
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

