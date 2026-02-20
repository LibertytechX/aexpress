import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MailgunEmailService:
    @staticmethod
    def send_onboarding_email(email, first_name, password):
        """
        Sends an onboarding email to a new driver with their generated password.
        """
        if not all([settings.MAILGUN_DOMAIN, settings.MAILGUN_APIKEY]):
            logger.error("Mailgun settings are not fully configured.")
            return False

        api_url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"

        subject = "Welcome to Assured Express - Your Driver Account"

        # Simple HTML template for credentials
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
            <h2 style="color: #333;">Welcome, {first_name}!</h2>
            <p>Your driver account for Assured Express has been created.</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Username (Phone):</strong> [Your registered phone number]</p>
                <p style="margin: 10px 0 0 0;"><strong>Password:</strong> <span style="font-family: monospace; font-size: 1.2em;">{password}</span></p>
            </div>
            
            <p>Please use these credentials to log in to the Dispatcher Portal and update your password after your first login.</p>
            
            <p style="margin-top: 20px; font-size: 0.9em; color: #777;">
                If you have any questions, please contact the support team.
            </p>
            <p style="text-align: center; font-size: 0.8em; color: #999;">
                &copy; {{}} Assured Express. All rights reserved.
            </p>
        </div>
        """

        email_data = {
            "from": f"Assured Express <mailgun@{settings.MAILGUN_DOMAIN}>",
            "to": [email],
            "subject": subject,
            "html": html_body,
        }

        try:
            response = requests.post(
                api_url,
                auth=("api", settings.MAILGUN_APIKEY),
                data=email_data,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Onboarding email sent successfully to {email}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send onboarding email to {email}: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Mailgun response: {e.response.text}")
            return False
