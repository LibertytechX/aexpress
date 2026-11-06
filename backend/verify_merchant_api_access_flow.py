import os
import django
import sys
import json

# Setup Django
sys.path.append('/Users/mac/Liberty/aexpress/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from dispatcher.models import Merchant, MerchantAPIKey
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import Client

User = get_user_model()

def verify_access_request_flow():
    # 1. Setup Test User (Regular Merchant)
    email = "regular_merchant@example.com"
    phone = "09011111111"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "phone": phone,
            "business_name": "Regular Merchant",
            "contact_name": "Regular Handler",
            "usertype": "Merchant",
            "is_active": True
        }
    )
    user.set_password("password123")
    user.save()

    # Ensure it's a 'regular' merchant
    merchant, _ = Merchant.objects.get_or_create(user=user)
    merchant.merchant_type = "regular"
    merchant.save()

    print(f"User {email} ready with type 'regular'.")

    # 2. Get JWT Token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    client = Client()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    # 3. Test Request OTP (Should fail for 'regular' type)
    print("Testing Step 1: Request OTP as 'regular' merchant (Expected FAIL)...")
    response = client.post("/api/merchant/apikey/request-otp/", **headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 403:
        print("PASS: Access denied as expected.")
    else:
        print("FAIL: Access should have been denied.")
        return

    # 4. Request API Access
    print("Testing Step 2: Request API Access...")
    response = client.post("/api/merchant/request-api-access/", **headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("PASS: Access request successful.")
    else:
        print("FAIL: Access request failed.")
        return

    # 5. Verify Model Status
    merchant.refresh_from_db()
    if merchant.merchant_type == "api":
        print(f"Verified: merchant_type is now '{merchant.merchant_type}'.")
    else:
        print(f"FAIL: merchant_type is still '{merchant.merchant_type}'.")
        return

    # 6. Test Request OTP (Should now succeed)
    print("Testing Step 3: Request OTP as 'api' merchant (Expected PASS)...")
    response = client.post("/api/merchant/apikey/request-otp/", **headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("PASS: OTP requested successfully after status change.")
    else:
        print("FAIL: OTP request failed after status change.")

if __name__ == "__main__":
    verify_access_request_flow()
