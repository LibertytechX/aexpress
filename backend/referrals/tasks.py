import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils.dateparse import parse_datetime
from referrals.models import LibertyPayUser

logger = logging.getLogger(__name__)


@shared_task(name="referrals.tasks.sync_libertypay_users_task")
def sync_libertypay_users_task():
    """
    Fetches user data from LibertyPay API and syncs it to the LibertyPayUser model.
    """
    url = "https://backend.libertypayng.com/agency/user/get-with-sales-rep-code/"
    api_key = getattr(settings, "LIBERTYPAY_API_KEY", None)

    if not api_key:
        logger.error("LIBERTYPAY_API_KEY not found in settings")
        return "Error: LIBERTYPAY_API_KEY missing"

    headers = {
        "Authorization": f"ApiKey {api_key}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=300)
        response.raise_for_status()
        users_data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch users from LibertyPay API: {str(e)}")
        return f"Error: {str(e)}"

    if isinstance(users_data, dict) and "data" in users_data:
        users_data = users_data["data"]

    if not isinstance(users_data, list):
        logger.error(
            f"API response is not a list. Type: {type(users_data)}. Data: {str(users_data)[:500]}"
        )
        return f"Error: Unexpected API response format: {type(users_data)}"

    sync_count = 0
    for user_data in users_data:
        try:
            # Parse dates
            date_joined_str = user_data.get("date_joined")
            date_joined = parse_datetime(date_joined_str) if date_joined_str else None

            last_login_str = user_data.get("last_login")
            last_login = parse_datetime(last_login_str) if last_login_str else None

            LibertyPayUser.objects.update_or_create(
                id=user_data["id"],
                defaults={
                    "email": user_data.get("email"),
                    "referral_code": user_data.get("referral_code"),
                    "phone_number": user_data.get("phone_number"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "username": user_data.get("username"),
                    "date_joined": date_joined,
                    "last_login": last_login,
                },
            )
            sync_count += 1
        except Exception as e:
            logger.error(f"Error syncing user {user_data.get('id')}: {str(e)}")

    logger.info(f"Successfully synced {sync_count} LibertyPay users")
    return f"Success: Synced {sync_count} users"


@shared_task(name="referrals.tasks.send_buddy_referral_commission_task")
def send_buddy_referral_commission_task(referral_code: str, order_number: str):
    """
    Sends a buddy referral commission via LibertyPay API.
    """
    from referrals.models import LibertyPayUser

    buddy = LibertyPayUser.objects.filter(referral_code=referral_code).first()
    if not buddy:
        logger.error(f"Buddy with referral code {referral_code} not found")
        return f"Error: Buddy with referral code {referral_code} not found"

    if not buddy.phone_number:
        logger.error(f"Buddy with referral code {referral_code} has no phone number")
        return f"Error: Buddy with referral code {referral_code} has no phone number"

    url = "https://backend.libertypayng.com/send/send_money_paybuddy/"
    api_key = getattr(settings, "LIBERTYPAY_API_KEY", None)
    transaction_pin = getattr(settings, "LIBERTYPAY_TRANSACTION_PIN", "1234")

    if not api_key:
        logger.error("LIBERTYPAY_API_KEY not found in settings")
        return "Error: LIBERTYPAY_API_KEY missing"

    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "from_wallet_type": "COLLECTION",
        "to_wallet_type": "COLLECTION",
        "data": [
            {
                "buddy_phone_number": buddy.phone_number,
                "amount": 50.0,
                "narration": f"Buddy commission for order {order_number}",
                "is_beneficiary": True,
                "save_beneficiary": False,
                "remove_beneficiary": False,
                "is_recurring": False,
            }
        ],
        "transaction_pin": transaction_pin,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"Successfully sent buddy commission for order {order_number} to {buddy.phone_number}"
        )
        return f"Success: Commission sent to {buddy.phone_number}"
    except Exception as e:
        logger.error(
            f"Failed to send buddy commission for order {order_number}: {str(e)}"
        )
        return f"Error: {str(e)}"
