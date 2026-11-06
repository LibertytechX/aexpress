import os
import django
import json
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from orders.models import Order, Vehicle
from authentication.models import User
from wallet.models import Wallet, Charge, Transaction
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from orders.views import QuickSendView, OrderPayNowView
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def verify_refined_flow():
    print("--- Starting Verification of Refined Payment Flow ---")
    
    # 1. Setup User and Wallet
    user, _ = User.objects.get_or_create(
        email='merchant_test@example.com',
        defaults={'business_name': 'Test Merchant', 'phone': '07011112222'}
    )
    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet.balance = Decimal('0.00')
    wallet.save()
    
    # Ensure no old charges/orders interfere
    Charge.objects.filter(user=user).delete()
    Order.objects.filter(user=user).delete()

    print(f"User: {user.email}, Initial Balance: {wallet.balance}")

    # 2. Create Order (Quick Send)
    vehicle, _ = Vehicle.objects.get_or_create(name='Bike', defaults={'is_active': True, 'base_fare': 500, 'rate_per_km': 100, 'rate_per_minute': 10, 'max_weight_kg': 20, 'base_price': 500})
    
    factory = APIRequestFactory()
    data = {
        "vehicle": "Bike",
        "pickup_address": "Test Pickup",
        "sender_name": "Sender",
        "sender_phone": "08000000000",
        "payment_method": "cash",
        "distance_km": 5,
        "duration_minutes": 10,
        "dropoff_address": "Test Dropoff",
        "receiver_name": "Receiver",
        "receiver_phone": "09000000000"
    }
    
    request = factory.post('/api/orders/quick-send/', data=data, format='json')
    force_authenticate(request, user=user)
    
    response = QuickSendView.as_view()(request)
    if response.status_code != 201:
        print(f"FAILURE: Order creation failed: {response.data}")
        return

    order_number = response.data['order']['order_number']
    order = Order.objects.get(order_number=order_number)
    print(f"Order created: {order_number}, payment_info (should be null): {order.payment_info}")

    if order.payment_info:
         print("FAILURE: payment_info should be empty upon creation.")
         return

    # 3. Hit Pay Now
    print(f"Hitting Pay Now for order {order_number}...")
    request_pay = factory.post(f'/api/orders/{order_number}/pay-now/')
    force_authenticate(request_pay, user=user)
    
    response_pay = OrderPayNowView.as_view()(request_pay, order_number=order_number)
    if response_pay.status_code != 200:
        print(f"FAILURE: Pay Now failed: {response_pay.data}")
        return

    order.refresh_from_db()
    print(f"Pay Now Success. payment_info: {json.dumps(order.payment_info, indent=2)}")
    
    charge = Charge.objects.filter(order=order, user=user).first()
    if not charge or charge.status != 'pending':
        print(f"FAILURE: Pending charge not created correctly. Charge: {charge}")
        return
    print(f"Charge created: {charge.id}, Amount: {charge.amount}, Status: {charge.status}")

    # 4. Simulate Wallet Credit (Webhook Funding)
    funding_amount = order.total_amount + Decimal('1000.00')
    print(f"Simulating wallet credit of {funding_amount}...")
    
    # This should trigger Wallet.process_pending_charges via Wallet.credit
    wallet.credit(
        amount=funding_amount,
        description="Test Funding",
        reference="TEST-REF-123"
    )
    
    wallet.refresh_from_db()
    order.refresh_from_db()
    charge.refresh_from_db()
    
    print(f"New Balance: {wallet.balance} (Should be 1000.00 if {order.total_amount} was debited)")
    print(f"Order Payment Status: {order.payment_status} (Should be Paid)")
    print(f"Charge Status: {charge.status} (Should be completed)")
    
    expected_balance = Decimal('1000.00')
    if wallet.balance == expected_balance and order.payment_status == 'Paid' and charge.status == 'completed':
        print("\n🎉 SUCCESS: Entire refined payment flow verified!")
    else:
        print("\n❌ FAILURE: Flow verification failed.")

if __name__ == '__main__':
    verify_refined_flow()
