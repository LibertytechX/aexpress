import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from orders.models import Order, Vehicle
from riders.models import OrderOffer
from authentication.models import User
from decimal import Decimal


def verify():
    print("--- Verifying OrderOffer Creation Signal ---")

    # Get a user and vehicle
    user = User.objects.filter(usertype="Merchant").first()
    if not user:
        print("No merchant found!")
        return

    vehicle = Vehicle.objects.filter(is_active=True).first()
    if not vehicle:
        print("No active vehicle found!")
        return

    # Count existing offers for this order (none yet)
    initial_offers_count = OrderOffer.objects.count()
    print(f"Initial OrderOffer count: {initial_offers_count}")

    # Create a new order
    print(f"Creating order for user {user.phone} with vehicle {vehicle.name}...")
    order = Order.objects.create(
        user=user,
        vehicle=vehicle,
        pickup_address="Verification Pickup",
        sender_name="Verifier",
        sender_phone="123456789",
        total_amount=Decimal("1000.00"),
        payment_method="wallet",
    )
    print(f"Order created: {order.order_number}")

    # Check if OrderOffer was created
    new_offers_count = OrderOffer.objects.count()
    print(f"New OrderOffer count: {new_offers_count}")

    if new_offers_count > initial_offers_count:
        offer = OrderOffer.objects.filter(order=order).first()
        if offer:
            print("✓ SUCCESS: OrderOffer created automatically!")
            print(f"  Offer ID: {offer.id}")
            print(f"  Rider: {offer.rider}")
            print(f"  Estimated Earnings: {offer.estimated_earnings}")
            print(f"  Expires at: {offer.expires_at}")

            # Verify earnings is 80% (800.00)
            if offer.estimated_earnings == Decimal("800.00"):
                print(
                    "✓ SUCCESS: Estimated earnings correctly calculated as 80% (800.00)"
                )
            else:
                print(f"✗ FAILURE: Incorrect earnings: {offer.estimated_earnings}")
        else:
            print("✗ FAILURE: OrderOffer for the new order not found!")
    else:
        print("✗ FAILURE: No new OrderOffer created!")


if __name__ == "__main__":
    verify()
