import logging
import os
import requests
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Sum, Max, Prefetch
from django.template.loader import render_to_string
from celery import shared_task

from authentication.models import User, MerchantEmailLog
from orders.models import Order, Delivery

logger = logging.getLogger(__name__)

SENDER_EMAIL = "assuredxpressng@gmail.com"


def _send_marketing_email(merchant, template_code, subject, context=None):
    """Helper to render and send marketing emails, logging to prevent duplicates."""

    # Check if already sent
    if MerchantEmailLog.objects.filter(
        merchant=merchant, template_code=template_code
    ).exists():
        logger.info(f"Skipping {template_code} for {merchant.phone} - already sent.")
        return False

    context = context or {}
    context["merchant"] = merchant

    html_message = render_to_string(f"emails/marketing/{template_code}.html", context)

    # Get Mailgun credentials from environment
    api_key = os.getenv("MAILGUN_API_KEY") or os.getenv("MAILGUN_APIKEY")
    domain = os.getenv("MAILGUN_DOMAIN")
    from_email = os.getenv("MAILGUN_FROM_EMAIL", "noreply@mg.axpress.net")
    from_name = os.getenv("MAILGUN_FROM_NAME", "Assured Express")

    if not api_key or not domain:
        logger.error("Mailgun credentials not configured")
        return False

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [merchant.email],
                "subject": subject,
                "html": html_message,
                "text": "Please view this email in an HTML-compatible client.",
            },
        )

        if response.status_code == 200:
            # Log success
            MerchantEmailLog.objects.create(
                merchant=merchant, template_code=template_code
            )
            logger.info(
                f"Successfully sent {template_code} via Mailgun to {merchant.email}"
            )
            return True
        else:
            logger.error(
                f"Failed to send {template_code} via Mailgun to {merchant.email}: {response.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error sending {template_code} to {merchant.email}: {str(e)}")
        return False


@shared_task
def process_daily_drip_campaigns():
    """Evaluate merchants and run daily drip campaigns (A2, C1, B1-B2, C2, D1-D3)"""

    now = timezone.now()

    # Get all merchants
    merchants = User.objects.filter(usertype="Merchant", is_active=True).annotate(
        order_count=Count("orders")
    )

    for merchant in merchants:
        days_since_signup = (now - merchant.created_at).days

        # --- CATEGORY A: Onboarding ---

        # A2: Incomplete Signup (Day 1, missing verification)
        if days_since_signup == 1 and not (
            merchant.email_verified and merchant.phone_verified
        ):
            _send_marketing_email(
                merchant, "A2", "Complete your setup on Assured Express in 2 minutes"
            )
            continue  # If they haven't verified, don't send C1/other standard drips yet

        # If they haven't verified by day 1, we pause other campaigns until they do.
        if not (merchant.email_verified and merchant.phone_verified):
            continue

        # --- CATEGORY C1: Why Assured Express ---
        # C1: Day 1 after Welcome (Day 1)
        if days_since_signup == 1:
            _send_marketing_email(
                merchant, "C1", "The Merchant, and how delivery changed everything"
            )

        # --- CATEGORY B: Activation & Re-engagement ---

        # B1: First Delivery Nudge (Day 3)
        if days_since_signup == 3 and merchant.order_count == 0:
            _send_marketing_email(
                merchant,
                "B1",
                f"Your first delivery is waiting, {merchant.first_name or merchant.contact_name or 'there'} Let's get moving! 🚚",
            )

        # B2a: Re-engagement #1 (Day 14)
        if days_since_signup == 14 and merchant.order_count == 0:
            _send_marketing_email(
                merchant,
                "B2a",
                f"We miss you, {merchant.first_name or merchant.contact_name or 'there'} 👋",
            )

        # B2b: Re-engagement #2 (Day 16)
        if days_since_signup == 16 and merchant.order_count == 0:
            _send_marketing_email(
                merchant,
                "B2b",
                f"What's stopping you, {merchant.first_name or merchant.contact_name or 'there'}? Let's fix it together 🤝",
            )

        # B2c: Re-engagement #3 (Day 18)
        if days_since_signup == 18 and merchant.order_count == 0:
            _send_marketing_email(
                merchant,
                "B2c",
                f"{merchant.first_name or merchant.contact_name or 'Merchant'} — your account is ready when you are",
            )

        # --- CATEGORY C2 & D: Education and Coming Soon ---

        # C2: Delivery = Brand Trust (Day 20)
        if days_since_signup == 20:
            _send_marketing_email(
                merchant, "C2", "Your customers judge you by your delivery. 📦"
            )

        # D1: WebPOS Terminal (Day 22)
        if days_since_signup == 22:
            _send_marketing_email(
                merchant,
                "D1",
                "Big news: We're bringing POS terminals to your doorstep! 💳",
            )

        # D2: Business Loans (Day 24)
        if days_since_signup == 24:
            _send_marketing_email(
                merchant,
                "D2",
                "Capital when you need it most — no collateral, no stress 💼",
            )

        # D3: Accounting Suite (Day 26)
        if days_since_signup == 26:
            _send_marketing_email(
                merchant, "D3", "Stop guessing — start knowing your numbers 📊"
            )


@shared_task
def process_weekly_monday_reports():
    """Generates and sends weekly E1/E2 reports to all active merchants."""

    # Calculate previous Monday to Sunday
    now = timezone.now()
    today = now.date()
    # Assuming this runs on Monday morning (e.g. 8:00 AM)
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)

    start_date = last_monday.strftime("%b %d")
    end_date = last_sunday.strftime("%b %d")

    merchants = User.objects.filter(usertype="Merchant", is_active=True)

    for merchant in merchants:
        # Get orders from the past week
        weekly_orders = Order.objects.filter(
            user=merchant,
            created_at__date__gte=last_monday,
            created_at__date__lte=last_sunday,
        )

        total_requested = weekly_orders.count()

        if total_requested > 0:
            # E1: Active Merchant
            total_delivered = weekly_orders.filter(status="Done").count()
            success_rate = (
                int((total_delivered / total_requested) * 100) if total_requested else 0
            )

            # Find most active day
            from django.db.models.functions import ExtractIsoWeekDay

            most_active = (
                weekly_orders.annotate(weekday=ExtractIsoWeekDay("created_at"))
                .values("weekday")
                .annotate(count=Count("id"))
                .order_by("-count")
                .first()
            )

            day_map = {
                1: "Monday",
                2: "Tuesday",
                3: "Wednesday",
                4: "Thursday",
                5: "Friday",
                6: "Saturday",
                7: "Sunday",
            }
            most_active_day = (
                day_map.get(most_active["weekday"], "N/A") if most_active else "N/A"
            )

            # Find top delivery zone (simplification: we group by dropoff_address and pick the top one)
            # A more robust solution might use a true location/zone ID if available on the order/delivery
            top_delivery = (
                Delivery.objects.filter(order__in=weekly_orders)
                .values("dropoff_address")
                .annotate(count=Count("id"))
                .order_by("-count")
                .first()
            )

            top_zone = "your frequent destinations"
            if top_delivery and top_delivery["dropoff_address"]:
                # Simplistic way to extract city/area from address:
                address_parts = top_delivery["dropoff_address"].split(",")
                top_zone = (
                    address_parts[-1].strip()
                    if address_parts
                    else top_delivery["dropoff_address"][:30]
                )

            context = {
                "start_date": start_date,
                "end_date": end_date,
                "total_requested": total_requested,
                "total_delivered": total_delivered,
                "success_rate": success_rate,
                "most_active_day": most_active_day,
                "top_delivery_zone": top_zone,
            }

            _send_marketing_email(
                merchant, "E1", "Your Weekly Delivery Report 📊", context
            )
        else:
            # E2: Inactive Merchant
            _send_marketing_email(
                merchant,
                "E2",
                "See What You're Missing This Week on Assured Express 👀",
            )


@shared_task
def send_transactional_email(template_code, order_id):
    """Sends F1 or F2 transactional emails."""
    try:
        order = Order.objects.get(id=order_id)

        # A template_code F1 or F2 may be triggered multiple times (e.g., if re-dispatched),
        # so we don't necessarily want idempotency check from MerchantEmailLog unless strict.
        # But wait, we shouldn't spam F1 if order bounces between states.
        # Let's use it for F1/F2 but allow multiple by appending order_id to template_code
        specific_code = f"{template_code}_{order_id}"

        if MerchantEmailLog.objects.filter(
            merchant=order.user, template_code=specific_code
        ).exists():
            return False

        delivery = order.deliveries.first()  # Simplification for single-drop.

        context = {"order": order, "delivery": delivery}

        subject_map = {
            "F1": f"Your delivery is on the move! — Order #{order.order_number} 🚚",
            "F2": f"✅ Delivery Completed! — Order #{order.order_number} has arrived",
        }

        success = _send_marketing_email(
            order.user,
            template_code,
            subject_map.get(template_code, f"Update on Order #{order.order_number}"),
            context,
        )

        if success:
            MerchantEmailLog.objects.create(
                merchant=order.user, template_code=specific_code
            )

        return success
    except Exception as e:
        logger.error(
            f"Failed to send transactional email {template_code} for order {order_id}: {e}"
        )
        return False
