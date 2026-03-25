import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

BASE_URL = "https://api.360messenger.com"


def _get_api_key():
    return getattr(settings, "MESSENGER360_API_KEY", "")


def _headers():
    return {"Authorization": f"Bearer {_get_api_key()}"}


def send_message(phone_number, text, media_url=None):
    """
    Send a WhatsApp message via 360Messenger API.

    Args:
        phone_number: Recipient phone number (e.g. "2348012345678")
        text: Message text content
        media_url: Optional URL for image/document attachment

    Returns:
        dict with keys: success (bool), message_id (str), error (str)
    """
    url = f"{BASE_URL}/v2/sendMessage"
    payload = {
        "phonenumber": phone_number,
        "text": text,
    }
    if media_url:
        payload["url"] = media_url

    try:
        response = requests.post(url, data=payload, headers=_headers(), timeout=30)
        data = response.json()

        if response.status_code == 201 and data.get("success"):
            message_id = data.get("data", {}).get("id", "")
            logger.info(
                f"WhatsApp message sent to {phone_number}, id={message_id}"
            )
            return {
                "success": True,
                "message_id": message_id,
                "error": "",
            }

        error_msg = data.get("message", f"HTTP {response.status_code}")
        logger.warning(
            f"WhatsApp send failed for {phone_number}: {error_msg}"
        )
        return {"success": False, "message_id": "", "error": error_msg}

    except requests.RequestException as e:
        logger.error(f"WhatsApp API request error for {phone_number}: {e}")
        return {"success": False, "message_id": "", "error": str(e)}


def get_message_status(message_id):
    """
    Check delivery status of a sent message.

    Returns:
        dict with keys: status, statusInfo, delivery
    """
    url = f"{BASE_URL}/v2/message/status"
    try:
        response = requests.get(
            url, params={"id": message_id}, headers=_headers(), timeout=15
        )
        data = response.json()
        if data.get("success"):
            result = data.get("result", {})
            return {
                "status": result.get("status", "UNKNOWN"),
                "statusInfo": result.get("statusInfo", ""),
                "delivery": result.get("delivery", ""),
            }
        return {"status": "UNKNOWN", "statusInfo": "API error", "delivery": ""}
    except requests.RequestException as e:
        logger.error(f"WhatsApp status check error for {message_id}: {e}")
        return {"status": "UNKNOWN", "statusInfo": str(e), "delivery": ""}


def is_registered_user(phone_number):
    """
    Check if a phone number is registered on WhatsApp.

    Returns:
        bool
    """
    url = f"{BASE_URL}/v2/client/isRegisteredUser"
    try:
        response = requests.post(
            url,
            data={"contactId": phone_number},
            headers=_headers(),
            timeout=15,
        )
        data = response.json()
        return data.get("result", False)
    except requests.RequestException as e:
        logger.error(f"WhatsApp registration check error for {phone_number}: {e}")
        return False
