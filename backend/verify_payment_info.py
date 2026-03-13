import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aexpress.settings')
django.setup()

from orders.models import Order, Vehicle
from authentication.models import User
from wallet.models import Wallet, VirtualAccount
from django.test import RequestFactory
from orders.views import QuickSendView

def verify():
    # 1. Get or create a test user
    user, created = User.objects.get_or_create(
        email='test_merchant@example.com',
        defaults={
            'business_name': 'Test Business',
            'contact_name': 'Test User',
            'phone': '08012345678'
        }
    )
    if not created:
        user.business_name = 'Test Business'
        user.contact_name = 'Test User'
        user.phone = '08012345678'
        user.save()

    print(f"User: {user.email}")

    # 2. Get or create a vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        name='Bike',
        defaults={
            'max_weight_kg': 20,
            'base_fare': 500,
            'rate_per_km': 100,
            'rate_per_minute': 10,
            'is_active': True,
            'base_price': 500 # Legacy
        }
    )

    # 3. Create a request for QuickSendView
    factory = RequestFactory()
    data = {
        "vehicle": "Bike",
        "pickup_address": "123 Pickup St",
        "sender_name": "Test Sender",
        "sender_phone": "08011112222",
        "payment_method": "cash", # Use cash to avoid wallet/escrow logic complexity in this script
        "distance_km": 5,
        "duration_minutes": 15,
        "dropoff_address": "456 Dropoff Rd",
        "receiver_name": "Test Receiver",
        "receiver_phone": "08033334444"
    }
    
    request = factory.post('/api/orders/quick-send/', data=json.dumps(data), content_type='application/json')
    request.user = user

    # 4. Call the view
    view = QuickSendView.as_view()
    response = view(request)

    print(f"Response status: {response.status_code}")
    if response.status_code == 201:
        order_number = response.data['order']['order_number']
        order = Order.objects.get(order_number=order_number)
        print(f"Order created: {order_number}")
        print(f"Payment Info: {json.dumps(order.payment_info, indent=2)}")
        
        if order.payment_info and 'account_number' in order.payment_info:
            print("SUCCESS: payment_info is populated!")
        else:
            print("FAILURE: payment_info is empty or missing account_number")
    else:
        print(f"FAILURE: Response data: {response.data}")

if __name__ == '__main__':
    verify()
