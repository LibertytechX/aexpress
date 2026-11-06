import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from orders.models import Order

print("Checking first 10 orders for source field:")
orders = Order.objects.all().order_by('-created_at')[:10]
for o in orders:
    print(f"Order: {o.order_number}, Source: {o.source}")

# check if we can filter by source
merchant_orders = Order.objects.filter(source='merchant_web').count()
dispatcher_orders = Order.objects.filter(source='dispatcher_web').count()
print(f"Merchant Web Orders: {merchant_orders}")
print(f"Dispatcher Web Orders: {dispatcher_orders}")
