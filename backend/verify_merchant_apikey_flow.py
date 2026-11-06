import os
import django
import sys

# Setup Django
sys.path.append('/Users/mac/Liberty/aexpress/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from dispatcher.models import Merchant, MerchantAPIKey
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import Client
import json

User = get_user_model()

def verify_flow():
    # 1. Setup Test User
    email = "test_api_merchant@example.com"
    phone = "09000000000"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "phone": phone,
            "business_name": "Test API Merchant",
            "contact_name": "API Handler",
            "usertype": "Merchant",
            "is_active": True
        }
    )
    if not created:
        user.set_password("password123")
        user.save()
    else:
        user.set_password("password123")
        user.save()

    # Create/Update Merchant Profile
    merchant, _ = Merchant.objects.get_or_create(user=user)
    merchant.merchant_type = "api"
    merchant.save()

    print(f"User {email} ready with type 'api'.")

    # 2. Get JWT Token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    client = Client()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    # 3. Test Request OTP
    print("Testing Step 1: Request OTP...")
    response = client.post("/api/merchant/apikey/request-otp/", **headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("FAILED Step 1")
        return

    # 4. Fetch OTP from DB (to simulate email receipt)
    user.refresh_from_db()
    otp = user.otp
    print(f"Fetched OTP from DB: {otp}")

    # 5. Test Retrieve API Key
    print("Testing Step 2: Retrieve API Key...")
    data = {"otp": otp}
    response = client.post(
        "/api/merchant/apikey/retrieve/",
        data=json.dumps(data),
        content_type="application/json",
        **headers
    )
    print(f"Status: {response.status_code}")
    resp_json = response.json()
    print(f"Response: {resp_json}")

    if response.status_code == 200:
        api_key = resp_json.get("data", {}).get("api_key")
        if api_key and api_key.startswith("ak_live_"):
            print("SUCCESS: API Key retrieved correctly.")
        else:
            print("FAILED: API Key missing or invalid prefix.")
    else:
        print("FAILED Step 2")

    # 6. Verify Model Storage
    user.refresh_from_db()
    api_key_obj = MerchantAPIKey.objects.filter(merchant=user).first()
    if api_key_obj:
        print(f"Verified: MerchantAPIKey record exists (Prefix: {api_key_obj.prefix})")
    else:
        print("FAILED: MerchantAPIKey record not found in DB.")

if __name__ == "__main__":
    verify_flow()
