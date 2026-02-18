"""
Utility functions for the WhatsApp bot.
"""
import re
import requests
from django.conf import settings


def normalize_phone_number(phone):
    """
    Normalize phone number to standard format.
    Handles various formats: +2348012345678, 2348012345678, 08012345678
    Returns: 2348012345678 (without + prefix)
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if phone.startswith('234'):
        # Already in correct format
        return phone
    elif phone.startswith('0'):
        # Remove leading 0 and add 234
        return '234' + phone[1:]
    elif len(phone) == 10:
        # Assume it's missing country code
        return '234' + phone
    
    return phone


def format_currency(amount):
    """
    Format amount as Nigerian currency.
    Example: 45000 -> ₦45,000
    """
    return f"₦{amount:,.0f}"


def format_currency_short(amount):
    """
    Format amount with K for thousands.
    Example: 45000 -> ₦45K
    """
    if amount >= 1000:
        return f"₦{amount/1000:.0f}K"
    return f"₦{amount:.0f}"


def send_whatsapp_message(phone, message):
    """
    Send proactive WhatsApp message via respond.io API.
    
    Args:
        phone: Merchant phone number (normalized)
        message: Text message to send
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not settings.RESPOND_IO_API_KEY:
        # respond.io not configured, skip
        return False
    
    url = f"{settings.RESPOND_IO_BASE_URL}/contact/messages"
    headers = {
        "Authorization": f"Bearer {settings.RESPOND_IO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "phone": phone,
        "message": {
            "type": "text",
            "text": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        # Log error but don't fail
        print(f"Failed to send WhatsApp message: {e}")
        return False


def format_order_summary(order):
    """
    Format order details for bot response.
    
    Returns conversational summary like:
    "AX-6158265 — In Transit 🚴
    Ikeja → Lekki | ₦4,200"
    """
    status_emoji = {
        'pending': '⏳',
        'assigned': '👤',
        'picked_up': '📦',
        'in_transit': '🚴',
        'delivered': '✅',
        'cancelled': '❌'
    }
    
    emoji = status_emoji.get(order.status, '')
    status_text = order.get_status_display()
    
    # Extract area names from addresses (simplified)
    pickup_area = extract_area_from_address(order.pickup_address)
    
    # Get first dropoff area
    first_delivery = order.deliveries.first()
    dropoff_area = extract_area_from_address(first_delivery.dropoff_address) if first_delivery else "Unknown"
    
    return f"{order.order_number} — {status_text} {emoji}\n{pickup_area} → {dropoff_area} | {format_currency(order.total_amount)}"


def extract_area_from_address(address):
    """
    Extract area name from full address.
    Example: "15 Opebi Road, Ikeja, Lagos" -> "Ikeja"
    """
    if not address:
        return "Unknown"
    
    # Common Lagos areas
    areas = ['Ikeja', 'Lekki', 'V.I.', 'Victoria Island', 'Ikoyi', 'Yaba', 
             'Surulere', 'Ajah', 'Mainland', 'Island', 'Festac', 'Apapa']
    
    for area in areas:
        if area.lower() in address.lower():
            return area
    
    # Fallback: return first part after comma
    parts = address.split(',')
    if len(parts) > 1:
        return parts[1].strip()
    
    return address[:20] + '...' if len(address) > 20 else address

