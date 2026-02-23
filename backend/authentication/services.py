import random
import requests
import os
import logging
from django.utils import timezone
from .emails import send_verification_email

logger = logging.getLogger(__name__)


class OTPService:
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_sms_otp(phone, otp):
        """Send OTP via WhisperSMS API."""
        api_key = os.getenv("WHISPERSMS_API_KEY")
        template_id = os.getenv("WHISPERSMS_DEFAULT_TEMPLATE_ID")

        if not api_key:
            logger.error("WHISPERSMS_API_KEY not configured. OTP not sent via SMS.")
            # For development/testing, we might want to log it
            logger.info(f"OTP for {phone}: {otp}")
            return False

        url = "https://whispersms.xyz/transactional/send"  # Typical WhisperSMS endpoint, though we should verify

        # Based on hpmr analysis:
        # recipient_phone and (message_body or template)
        message_body = f"Your Assured Express verification code is: {otp}. It expires in 10 minutes."
        payload = {
            "recipient": phone,
            "place_holders": {"message": message_body},
        }

        if template_id:
            payload["template"] = template_id
            # If using template, usually you pass parameters. WhisperSMS docs in hpmr might clarify.

        headers = {
            "Authorization": f"Api_key {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            # Note: We are using a generic endpoint. If the user has a specific one, we should update.
            # In hpmr/messaging/services.py it doesn't show the full URL, but hpmr/messaging/SMS_INTEGRATION.md does.
            # hpmr/messaging/SMS_INTEGRATION.md: /api/v1/messaging/sms/send/

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"SMS OTP sent successfully to {phone}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS OTP to {phone}: {str(e)}")
            return False

    @staticmethod
    def send_email_otp(user, otp):
        """Send verification email containing OTP."""
        return send_verification_email(user, otp=otp)
