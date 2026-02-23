from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from dispatcher.models import Rider
from orders.models import Order, Delivery, Vehicle
from dispatcher.utils import emit_activity
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = "Assign all pending orders of a specific mode to a rider by phone number"

    def add_arguments(self, parser):
        parser.add_argument("phone", type=str, help="Rider's phone number")
        parser.add_argument(
            "--mode",
            type=str,
            choices=["quick", "multi"],
            default="quick",
            help="Order mode (quick or multi). Defaults to quick.",
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        mode = options["mode"]

        self.stdout.write(f"Assigning {mode} orders to rider with phone: {phone}")

        try:
            # 1. Find the user
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                raise CommandError(f"User with phone number {phone} does not exist.")

            # 2. Find the rider profile
            try:
                rider = Rider.objects.get(user=user)
            except Rider.DoesNotExist:
                raise CommandError(
                    f"User with phone {phone} is not registered as a Rider."
                )

            # 3. Fetch pending orders of the specified mode
            pending_orders = Order.objects.filter(status="Pending", mode=mode)
            count = pending_orders.count()

            if count == 0:
                self.stdout.write(
                    self.style.WARNING(f"No pending {mode} orders found. Creating a sample order...")
                )
                self.create_sample_order(mode)
                pending_orders = Order.objects.filter(status="Pending", mode=mode)
                count = pending_orders.count()

            self.stdout.write(
                f"Found {count} pending {mode} orders. Starting assignment..."
            )

            # 4. Atomically assign orders
            assigned_count = 0
            with transaction.atomic():
                for order in pending_orders:
                    order.rider = rider
                    order.status = "Assigned"
                    order.save()

                    # Emit activity for tracking
                    emit_activity(
                        event_type="assigned",
                        order_id=order.order_number,
                        text=f"Order {order.order_number} assigned to {user.get_full_name()} via management command",
                        color="blue",
                        metadata={
                            "rider_id": str(rider.id),
                            "rider_name": user.get_full_name(),
                            "assigned_via": "management_command",
                        },
                    )
                    assigned_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully assigned {assigned_count} orders to {user.get_full_name()} ({rider.rider_id})"
                )
            )
        except Exception as e:
            if isinstance(e, CommandError):
                raise e
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())

    def create_sample_order(self, mode):
        """Create a sample merchant, vehicle, and pending order."""
        # 1. Get or create a sample merchant
        merchant, _ = User.objects.get_or_create(
            phone="+234811222333",
            defaults={
                "email": "sample_merchant@example.com",
                "business_name": "Sample Store",
                "contact_name": "Sample Merchant",
                "usertype": "Merchant"
            }
        )

        # 2. Get or create a sample vehicle
        vehicle, _ = Vehicle.objects.get_or_create(
            name="Sample Bike",
            defaults={"max_weight_kg": 50, "base_price": 500, "base_fare": 500}
        )

        # 3. Create the order
        order = Order.objects.create(
            user=merchant,
            mode=mode,
            status="Pending",
            vehicle=vehicle,
            pickup_address="123 Sample Street, Ikeja, Lagos",
            sender_name="Sample Store",
            sender_phone="+234811222333",
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("5.0"),
            duration_minutes=20
        )

        # 4. Create a delivery for the order
        Delivery.objects.create(
            order=order,
            dropoff_address="456 Sample Road, Victoria Island, Lagos",
            receiver_name="Sample Receiver",
            receiver_phone="+234800999888",
            package_type="Box"
        )

        self.stdout.write(self.style.SUCCESS(f"Created sample {mode} order: {order.order_number}"))
