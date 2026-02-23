import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def emit_activity(event_type, order_id, text, color="gold", metadata=None):
    """
    Write an ActivityFeed row and publish it to Ably channel 'dispatch-feed'.
    This must NEVER raise — a failure here should not break the calling request.
    """
    from .models import ActivityFeed

    if metadata is None:
        metadata = {}

    # 1. Persist to DB (source of truth)
    try:
        entry = ActivityFeed.objects.create(
            event_type=event_type,
            order_id=order_id,
            text=text,
            color=color,
            metadata=metadata,
        )
    except Exception as exc:
        logger.error(f"emit_activity: DB write failed for {order_id}: {exc}")
        return

    # 2. Publish to Ably
    try:
        api_key = getattr(settings, "ABLY_API_KEY", "")
        if not api_key:
            logger.warning("emit_activity: ABLY_API_KEY not configured, skipping publish")
            return

        import asyncio
        from ably import AblyRest

        payload = {
            "id": str(entry.id),
            "event_type": entry.event_type,
            "order_id": entry.order_id,
            "text": entry.text,
            "color": entry.color,
            "metadata": entry.metadata,
            "created_at": entry.created_at.isoformat(),
        }

        async def _publish():
            client = AblyRest(api_key)
            channel = client.channels.get("dispatch-feed")
            await channel.publish("activity", payload)

        asyncio.run(_publish())
        logger.info(f"emit_activity: published [{event_type}] {order_id}")
    except Exception as exc:
        logger.error(f"emit_activity: Ably publish failed for {order_id}: {exc}")


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
