#!/usr/bin/env python
"""
Test script for Wallet System API endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test credentials
PHONE = "08099999999"
PASSWORD = "admin123"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print(f"{'='*60}\n")

def main():
    print("\n🧪 TESTING WALLET SYSTEM API\n")

    # Step 1: Login
    print("Step 1: Login to get access token...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "phone": PHONE,
        "password": PASSWORD
    })
    print_response("LOGIN", login_response)

    if login_response.status_code != 200:
        print("❌ Login failed! Cannot proceed with tests.")
        return

    access_token = login_response.json()['tokens']['access']
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Step 2: Get wallet balance
    print("\nStep 2: Get wallet balance...")
    balance_response = requests.get(f"{BASE_URL}/api/wallet/balance/", headers=headers)
    print_response("WALLET BALANCE", balance_response)

    if balance_response.status_code == 200:
        wallet_data = balance_response.json()['data']
        print(f"✅ Current Balance: ₦{wallet_data['balance']}")

    # Step 3: Get transaction history
    print("\nStep 3: Get transaction history...")
    transactions_response = requests.get(f"{BASE_URL}/api/wallet/transactions/", headers=headers)
    print_response("TRANSACTION HISTORY", transactions_response)

    if transactions_response.status_code == 200:
        response_data = transactions_response.json()
        transactions = response_data.get('results', {}).get('data', [])
        print(f"✅ Total Transactions: {len(transactions)}")

    # Step 4: Initialize payment (Paystack)
    print("\nStep 4: Initialize wallet funding (Paystack)...")
    print("⚠️  Note: This will fail if PAYSTACK_SECRET_KEY is not set in .env")
    fund_response = requests.post(f"{BASE_URL}/api/wallet/fund/initialize/",
        headers=headers,
        json={"amount": "5000.00"}
    )
    print_response("INITIALIZE PAYMENT", fund_response)

    if fund_response.status_code == 200:
        payment_data = fund_response.json()['data']
        print(f"✅ Payment URL: {payment_data['authorization_url']}")
        print(f"✅ Reference: {payment_data['reference']}")
        print("\n📝 To complete payment:")
        print(f"   1. Visit: {payment_data['authorization_url']}")
        print(f"   2. Complete payment")
        print(f"   3. Verify using reference: {payment_data['reference']}")

    # Step 5: Test wallet payment for order
    print("\nStep 5: Test order creation with wallet payment...")
    print("⚠️  This will fail if wallet balance is insufficient")

    # Get vehicles first
    vehicles_response = requests.get(f"{BASE_URL}/api/orders/vehicles/", headers=headers)
    if vehicles_response.status_code == 200:
        vehicles = vehicles_response.json()['vehicles']
        if vehicles:
            vehicle_name = vehicles[0]['name']
            vehicle_price = vehicles[0]['base_price']

            print(f"Using vehicle: {vehicle_name} (₦{vehicle_price})")

            order_response = requests.post(f"{BASE_URL}/api/orders/quick-send/",
                headers=headers,
                json={
                    "vehicle": vehicle_name,
                    "pickup_address": "Test Pickup Address",
                    "sender_name": "Test Sender",
                    "sender_phone": "08012345678",
                    "dropoff_address": "Test Dropoff Address",
                    "receiver_name": "Test Receiver",
                    "receiver_phone": "08087654321",
                    "payment_method": "wallet",
                    "package_type": "Box"
                }
            )
            print_response("CREATE ORDER WITH WALLET PAYMENT", order_response)

            if order_response.status_code == 201:
                print("✅ Order created and wallet debited successfully!")
            elif order_response.status_code == 400:
                error_data = order_response.json()
                if 'wallet' in error_data.get('errors', {}):
                    print(f"❌ {error_data['errors']['wallet'][0]}")

    # Step 6: Check balance again
    print("\nStep 6: Check wallet balance after order...")
    balance_response2 = requests.get(f"{BASE_URL}/api/wallet/balance/", headers=headers)
    print_response("WALLET BALANCE (AFTER ORDER)", balance_response2)

    if balance_response2.status_code == 200:
        wallet_data2 = balance_response2.json()['data']
        print(f"✅ New Balance: ₦{wallet_data2['balance']}")

    # Step 7: Get updated transaction history
    print("\nStep 7: Get updated transaction history...")
    transactions_response2 = requests.get(f"{BASE_URL}/api/wallet/transactions/", headers=headers)
    print_response("UPDATED TRANSACTION HISTORY", transactions_response2)

    if transactions_response2.status_code == 200:
        response_data2 = transactions_response2.json()
        transactions2 = response_data2.get('results', {}).get('data', [])
        print(f"✅ Total Transactions: {len(transactions2)}")

    print("\n✅ WALLET SYSTEM TESTS COMPLETED!\n")

if __name__ == "__main__":
    main()

