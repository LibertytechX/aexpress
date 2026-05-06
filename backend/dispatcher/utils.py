import requests
import logging
import base64
import json
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
            logger.warning(
                "emit_activity: ABLY_API_KEY not configured, skipping publish"
            )
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
        if not all([settings.MAILGUN_DOMAIN, settings.MAILGUN_API_KEY]):
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
                auth=("api", settings.MAILGUN_API_KEY),
                data=email_data,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Onboarding email sent successfully to {email}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send onboarding email to {email} via Mailgun: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Mailgun response: {e.response.text}")
            
            # Fallback to MailNow
            logger.info(f"Attempting fallback to MailNow for {email}")
            return MailNowService.send_email(
                from_email=f"Assured Express <mailgun@{settings.MAILGUN_DOMAIN}>",
                to_email=email,
                subject=subject,
                text=None,
                html=html_body
            )

    @staticmethod
    def send_csv_attachment_email(email, csv_content, filename, subject, body):
        """
        Sends an email with a CSV attachment using Mailgun.
        """
        if not all([settings.MAILGUN_DOMAIN, settings.MAILGUN_API_KEY]):
            logger.error("Mailgun settings are not fully configured.")
            return False

        api_url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"

        try:
            response = requests.post(
                api_url,
                auth=("api", settings.MAILGUN_API_KEY),
                files=[("attachment", (filename, csv_content))],
                data={
                    "from": f"Assured Express <mailgun@{settings.MAILGUN_DOMAIN}>",
                    "to": [email],
                    "subject": subject,
                    "text": body,
                    "html": f"<html><body><p>{body}</p></body></html>",
                },
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"CSV export email sent successfully to {email}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send CSV export email to {email} via Mailgun: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Mailgun response: {e.response.text}")
            
            # Fallback to MailNow
            logger.info(f"Attempting fallback to MailNow for {email}")
            attachments = [
                {
                    "filename": filename,
                    "content": base64.b64encode(csv_content.encode() if isinstance(csv_content, str) else csv_content).decode('utf-8'),
                    "content_type": "text/csv"
                }
            ]
            return MailNowService.send_email(
                from_email=f"Assured Express <mailgun@{settings.MAILGUN_DOMAIN}>",
                to_email=email,
                subject=subject,
                text=body,
                attachments=attachments
            )


class MailNowService:
    """
    Utility service to send emails via MailNow API.
    Used as a fallback for Mailgun.
    """

    @staticmethod
    def send_email(from_email, to_email, subject, text, html=None, attachments=None):
        """
        Sends an email using the MailNow API.
        """
        if not all([settings.MAILNOW_API_URL, settings.MAILNOW_API_KEY]):
            logger.error("MailNow settings are not fully configured.")
            return False

        payload = {
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "text": text,
        }
        if html:
            payload["html"] = html
        if attachments:
            payload["attachments"] = attachments

        try:
            response = requests.post(
                settings.MAILNOW_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": settings.MAILNOW_API_KEY,
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Email sent successfully to {to_email} via MailNow")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email to {to_email} via MailNow: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"MailNow response: {e.response.text}")
            return False


def find_closest_zone(lat, lng):
    """
    Find the closest active Zone to a given (lat, lng) point.
    Uses Google Maps Distance Matrix API for road distance,
    falling back to Haversine (great-circle) distance if API fails or is not configured.
    """
    from .models import Zone
    from django.conf import settings
    import requests

    zones = list(Zone.objects.filter(is_active=True))
    if not zones:
        return None

    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
    if api_key:
        try:
            # Prepare Distance Matrix request
            origins = f"{lat},{lng}"
            destinations = "|".join([f"{z.center_lat},{z.center_lng}" for z in zones])

            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": origins,
                "destinations": destinations,
                "key": api_key,
                "mode": "driving",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK":
                results = data["rows"][0]["elements"]
                min_distance = float("inf")
                closest_index = -1

                for i, res in enumerate(results):
                    if res.get("status") == "OK":
                        # distance['value'] is in meters
                        dist_val = res["distance"]["value"]
                        if dist_val < min_distance:
                            min_distance = dist_val
                            closest_index = i

                if closest_index != -1:
                    logger.info(
                        f"find_closest_zone: Found closest zone '{zones[closest_index].name}' via Google Maps (dist: {min_distance}m)"
                    )
                    return zones[closest_index]

        except Exception as e:
            logger.error(f"find_closest_zone: Google Maps Distance Matrix failed: {e}")

    # Fallback to Haversine distance
    closest = None
    min_dist = float("inf")
    for zone in zones:
        dist = Zone.haversine_distance(lat, lng, zone.center_lat, zone.center_lng)
        if dist < min_dist:
            min_dist = dist
            closest = zone

    if closest:
        logger.info(
            f"find_closest_zone: Found closest zone '{closest.name}' via Haversine (dist: {min_dist:.2f}km)"
        )
    return closest


def generate_notification_id() -> int:
    from .models import MerchantNotification

    count = MerchantNotification.objects.all().count() + 1
    return count
