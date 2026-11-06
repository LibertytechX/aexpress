import os
import django
import sys

# Setup django environment
sys.path.append('/Users/mac/Liberty/aexpress/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from dispatcher.utils import MailgunEmailService, MailNowService
from django.conf import settings
# import responses # Using responses if available, or just mock it manually

def test_fallback():
    print("Testing MailNow fallback...")
    
    # Test 1: Call MailNow directly
    print("\n1. Testing MailNowService.send_email directly...")
    success = MailNowService.send_email(
        from_email="test@example.com",
        to_email="receiver@example.com",
        subject="Direct Test",
        text="Hello MailNow"
    )
    print(f"Direct call result: {success} (Expected False if 127.0.0.1:3200 is down, but should log the attempt)")

    # Test 2: Trigger fallback in MailgunEmailService
    print("\n2. Testing Mailgun fallback (Mailgun will fail because of dummy settings)...")
    # Backup settings
    old_key = settings.MAILGUN_API_KEY
    settings.MAILGUN_API_KEY = "invalid-key"
    
    try:
        success = MailgunEmailService.send_onboarding_email(
            email="fallback@example.com",
            first_name="Test",
            password="password123"
        )
        print(f"Fallback call result: {success}")
    finally:
        settings.MAILGUN_API_KEY = old_key

if __name__ == "__main__":
    test_fallback()
