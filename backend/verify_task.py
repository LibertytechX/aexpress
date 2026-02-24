import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from riders.tasks import publish_random_order_offer
from riders.models import OrderOffer
from django.utils import timezone
from datetime import timedelta


def verify():
    print("Checking for pending order offers...")
    pending_offers = OrderOffer.objects.filter(status="pending")
    count = pending_offers.count()
    print(f"Found {count} pending offers.")

    if count == 0:
        print("Creating a dummy pending order offer for testing...")
        from orders.models import Order, Vehicle
        from authentication.models import User

        user = User.objects.first()
        vehicle = Vehicle.objects.first()
        if not user or not vehicle:
            print("Cannot create test offer: User or Vehicle missing.")
            return

        order = Order.objects.create(
            user=user,
            vehicle=vehicle,
            total_amount=1000,
            pickup_address="Test Pickup",
            sender_name="Test Sender",
            sender_phone="08012345678",
        )

        offer = OrderOffer.objects.create(
            order=order,
            status="pending",
            expires_at=timezone.now() + timedelta(minutes=15),
            estimated_earnings=800,
        )
        print(f"Created test offer: {offer.id}")

    print("Triggering publish_random_order_offer task...")
    result = publish_random_order_offer()
    print(f"Task returned: {result}")
    print("Check backend logs for Ably publication status.")


if __name__ == "__main__":
    verify()
