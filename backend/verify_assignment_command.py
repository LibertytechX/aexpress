import os
import django
import sys
from decimal import Decimal

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from authentication.models import User
from dispatcher.models import Rider, ActivityFeed
from orders.models import Order, Vehicle


def verify_command():
    print("Setting up verification data...")
    phone = "+234999111222"

    # 1. Cleanup old data
    User.objects.filter(phone=phone).delete()
    Order.objects.filter(sender_phone="verification_test").delete()

    # 2. Create Rider
    user = User.objects.create_user(
        phone=phone,
        email="verify_rider@example.com",
        password="password123",
        contact_name="Verify Rider",
        usertype="Rider",
    )
    # Rider profile NOT created via signal, create it manually
    rider = Rider.objects.create(user=user, status="online")

    # 3. Create Vehicle
    vehicle, _ = Vehicle.objects.get_or_create(
        name="Verification Bike",
        defaults={"max_weight_kg": 50, "base_price": 500, "base_fare": 500},
    )

    # 4. Create Merchant for orders
    merchant, _ = User.objects.get_or_create(
        phone="+234888777666",
        defaults={
            "email": "verify_merchant@example.com",
            "business_name": "Verify Store",
        },
    )

    # 5. Create Pending Orders
    Order.objects.create(
        user=merchant,
        mode="quick",
        status="Pending",
        vehicle=vehicle,
        total_amount=Decimal("1000.00"),
        sender_phone="verification_test",
    )
    Order.objects.create(
        user=merchant,
        mode="quick",
        status="Pending",
        vehicle=vehicle,
        total_amount=Decimal("1000.00"),
        sender_phone="verification_test",
    )
    Order.objects.create(
        user=merchant,
        mode="multi",
        status="Pending",
        vehicle=vehicle,
        total_amount=Decimal("2000.00"),
        sender_phone="verification_test",
    )

    print("Original Pending Orders:")
    print(f"Quick: {Order.objects.filter(status='Pending', mode='quick').count()}")
    print(f"Multi: {Order.objects.filter(status='Pending', mode='multi').count()}")

    # 6. Run Command for Quick Mode
    print(
        f"\nRunning command: python manage.py assign_rider_orders {phone} --mode quick"
    )
    from django.core.management import call_command

    call_command("assign_rider_orders", phone, mode="quick")

    # 7. Verify Quick assignments
    assigned_quick = Order.objects.filter(
        rider=rider, mode="quick", status="Assigned"
    ).count()
    remaining_pending_quick = Order.objects.filter(
        status="Pending", mode="quick"
    ).count()
    remaining_pending_multi = Order.objects.filter(
        status="Pending", mode="multi"
    ).count()

    print(f"\nVerification Results (Quick):")
    print(f"Assigned Quick: {assigned_quick} (Expected 2)")
    print(f"Remaining Pending Quick: {remaining_pending_quick} (Expected 0)")
    print(f"Remaining Pending Multi: {remaining_pending_multi} (Expected 1)")

    # 8. Run Command for Multi Mode
    print(
        f"\nRunning command: python manage.py assign_rider_orders {phone} --mode multi"
    )
    call_command("assign_rider_orders", phone, mode="multi")

    # 9. Verify Multi assignments
    assigned_multi = Order.objects.filter(
        rider=rider, mode="multi", status="Assigned"
    ).count()
    remaining_pending_all = Order.objects.filter(status="Pending").count()

    print(f"\nVerification Results (Multi):")
    print(f"Assigned Multi: {assigned_multi} (Expected 1)")
    print(f"Remaining Pending All: {remaining_pending_all} (Expected 0)")

    # 10. Check Activity Feed
    feed_count = ActivityFeed.objects.filter(
        metadata__assigned_via="management_command",
        metadata__rider_name=user.get_full_name(),
    ).count()
    print(f"\nActivity Feed entries: {feed_count} (Expected 3)")

    if (
        assigned_quick == 2
        and assigned_multi == 1
        and remaining_pending_all == 0
        and feed_count == 3
    ):
        print("\n✅ VERIFICATION SUCCESSFUL")
    else:
        print("\n❌ VERIFICATION FAILED")


if __name__ == "__main__":
    verify_command()
