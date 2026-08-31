import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from orders.models import Order, Vehicle
from dispatcher.serializers import OrderCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

User = get_user_model()
user = User.objects.filter(usertype='Dispatcher').first()
vehicle = Vehicle.objects.first()

data = {
    "pickup": "123 Dispatch St",
    "dropoff": "456 Customer Ave",
    "senderName": "Dispatcher User",
    "senderPhone": "08012345678",
    "receiverName": "Happy Customer",
    "receiverPhone": "08087654321",
    "vehicle": vehicle.name,
    "packageType": "Box",
    "price": 1500,
    "manual_price": True,
    "distance_km": 5.5,
    "duration_minutes": 20,
    "is_relay_order": False,
    "pickup_lat": 6.5244,
    "pickup_lng": 3.3792,
    "dropoff_lat": 6.5244,
    "dropoff_lng": 3.3792
}

factory = APIRequestFactory()
request = factory.post('/api/dispatcher/orders/', data)
request.user = user

# Use the merchant ID found earlier
data["merchantId"] = "243982"

serializer = OrderCreateSerializer(data=data, context={'request': request})
if serializer.is_valid():
    order = serializer.save()
    print(f"Created order: {order.order_number}, Source: {order.source}")
    if order.source == 'dispatcher_web':
        print("SUCCESS: Source correctly set to dispatcher_web")
    else:
        print(f"FAILURE: Source is {order.source}")
else:
    print(f"Serializer errors: {serializer.errors}")
