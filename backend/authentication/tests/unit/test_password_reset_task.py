"""Unit tests for send_password_reset_otp_task Celery task."""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from authentication.models import User
from authentication.tasks import send_password_reset_otp_task


class SendPasswordResetOtpTaskUnitTest(TestCase):
    """Unit tests verifying OTP dispatch via email and SMS in background task."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="reset_unit@example.com",
            phone="+2348011223344",
            password="StrongPassword123!",
            contact_name="Reset User",
            business_name="Reset Logistics",
        )
        self.user.password_reset_token = "123456"
        self.user.save(update_fields=["password_reset_token"])

    @patch("authentication.tasks.send_password_reset_otp_to_email")
    @patch("authentication.tasks.OTPService.send_sms_otp")
    def test_send_password_reset_otp_task_sends_to_both_email_and_phone(
        self, mock_send_sms, mock_send_email
    ):
        """Verify OTP task sends to both email and phone regardless of input channel."""
        mock_send_email.return_value = True
        mock_send_sms.return_value = True

        result = send_password_reset_otp_task(str(self.user.id))

        self.assertEqual(result, {"email_sent": True, "sms_sent": True})
        mock_send_email.assert_called_once_with(self.user)
        mock_send_sms.assert_called_once_with(phone=self.user.phone, otp="123456")

    @patch("authentication.tasks.send_password_reset_otp_to_email")
    @patch("authentication.tasks.OTPService.send_sms_otp")
    def test_send_password_reset_otp_task_missing_user(
        self, mock_send_sms, mock_send_email
    ):
        """Verify task handles non-existent user ID gracefully."""
        result = send_password_reset_otp_task("00000000-0000-0000-0000-000000000000")

        self.assertFalse(result)
        mock_send_email.assert_not_called()
        mock_send_sms.assert_not_called()

    @patch("authentication.tasks.send_password_reset_otp_to_email")
    @patch("authentication.tasks.OTPService.send_sms_otp")
    def test_send_password_reset_otp_task_preps_otp_if_missing(
        self, mock_send_sms, mock_send_email
    ):
        """Verify task auto-generates OTP if user does not have a token yet."""
        self.user.password_reset_token = None
        self.user.save(update_fields=["password_reset_token"])

        mock_send_email.return_value = True
        mock_send_sms.return_value = True

        result = send_password_reset_otp_task(str(self.user.id))

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)
        self.assertEqual(len(self.user.password_reset_token), 6)
        self.assertEqual(result, {"email_sent": True, "sms_sent": True})
        mock_send_email.assert_called_once_with(self.user)
        mock_send_sms.assert_called_once_with(
            phone=self.user.phone, otp=self.user.password_reset_token
        )

    @patch("authentication.tasks.send_password_reset_otp_to_email", side_effect=Exception("Email error"))
    @patch("authentication.tasks.OTPService.send_sms_otp")
    def test_send_password_reset_otp_task_email_failure_does_not_break_sms(
        self, mock_send_sms, mock_send_email
    ):
        """Verify email error does not prevent SMS from being sent."""
        mock_send_sms.return_value = True

        result = send_password_reset_otp_task(str(self.user.id))

        self.assertEqual(result, {"email_sent": False, "sms_sent": True})
        mock_send_sms.assert_called_once_with(phone=self.user.phone, otp="123456")

    @patch("authentication.tasks.send_password_reset_otp_to_email")
    @patch("authentication.tasks.OTPService.send_sms_otp", side_effect=Exception("SMS error"))
    def test_send_password_reset_otp_task_sms_failure_does_not_break_email(
        self, mock_send_sms, mock_send_email
    ):
        """Verify SMS error does not prevent email from being sent."""
        mock_send_email.return_value = True

        result = send_password_reset_otp_task(str(self.user.id))

        self.assertEqual(result, {"email_sent": True, "sms_sent": False})
        mock_send_email.assert_called_once_with(self.user)
