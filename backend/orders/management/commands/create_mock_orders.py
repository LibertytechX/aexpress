import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from authentication.models import User
from orders.models import Order, Delivery, OrderEvent, Vehicle
from dispatcher.models import Rider

class Command(BaseCommand):
    help = "Generate mock orders, deliveries, and associated order events."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of mock orders to create",
        )

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(f"Generating {count} mock orders...")

        merchants = list(User.objects.filter(usertype="Merchant"))
        if not merchants:
            self.stdout.write(self.style.ERROR("No merchants found. Please create a merchant user first."))
            return

        riders = list(Rider.objects.filter(is_active=True))
        if not riders:
            self.stdout.write(self.style.WARNING("No active riders found. Orders will remain unassigned or have random assignment data."))

        vehicles = list(Vehicle.objects.all())
        if not vehicles:
            self.stdout.write(self.style.ERROR("No vehicles found. Please run 'python manage.py seed_vehicles' first."))
            return

        addresses = [
            "123 Mockingbird Lane, Ikeja",
            "456 fake Street, Lekki",
            "789 imaginary Road, Victoria Island",
            "321 Dummy Avenue, Surulere",
            "654 Null Boulevard, Yaba",
        ]

        names = ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis"]

        for i in range(count):
            try:
                with transaction.atomic():
                    merchant = random.choice(merchants)
                    vehicle = random.choice(vehicles)
                    rider = random.choice(riders) if riders else None
                    
                    # Randomly pick a status for the order
                    status_options = ["Pending", "Assigned", "Started", "Pickup", "Fulfilling", "Arrived", "Done"]
                    final_status = random.choice(status_options)
                    
                    order = Order.objects.create(
                        user=merchant,
                        mode=random.choice(["quick", "multi"]),
                        vehicle=vehicle,
                        pickup_address=random.choice(addresses),
                        pickup_latitude=6.45 + (random.random() * 0.1),
                        pickup_longitude=3.35 + (random.random() * 0.1),
                        sender_name=merchant.business_name or merchant.get_full_name(),
                        sender_phone=merchant.phone,
                        payment_method=random.choice(["wallet", "cash", "receiver_pays"]),
                        payment_status="Paid" if final_status == "Done" else "Pending",
                        total_amount=Decimal(random.randint(500, 5000)),
                        distance_km=Decimal(round(random.uniform(1.0, 15.0), 2)),
                        duration_minutes=random.randint(10, 60),
                        status=final_status,
                        rider=rider if final_status != "Pending" else None,
                    )

                    # Create a delivery
                    Delivery.objects.create(
                        order=order,
                        dropoff_address=random.choice(addresses),
                        dropoff_latitude=6.45 + (random.random() * 0.1),
                        dropoff_longitude=3.35 + (random.random() * 0.1),
                        receiver_name=random.choice(names),
                        receiver_phone=f"+23480{random.randint(10000000, 99999999)}",
                        package_type=random.choice(["Box", "Envelope", "Fragile", "Food"]),
                        status="Delivered" if final_status == "Done" else "Pending",
                    )

                    # Create Order Events based on status
                    self.create_events_for_order(order, final_status, merchant, rider)

                    self.stdout.write(self.style.SUCCESS(f"Created order {order.order_number} with status {final_status}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create order {i+1}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} mock orders."))

    def create_events_for_order(self, order, status, merchant, rider):
        """Creates a sequence of events leading up to the current status."""
        
        # Always created
        OrderEvent.objects.create(
            order=order,
            event="Created",
            description=f"Order created by {merchant.get_full_name()}",
            created_by=merchant
        )

        if status == "Pending":
            return

        # If it's not pending, it must have been assigned
        OrderEvent.objects.create(
            order=order,
            event="Assigned",
            description=f"Order assigned to rider {rider.user.get_full_name() if rider else 'Unknown'}",
            created_at=timezone.now() - timezone.timedelta(minutes=30)
        )

        if status == "Assigned":
            return

        # Started
        OrderEvent.objects.create(
            order=order,
            event="Started",
            description="Rider started the order",
            created_at=timezone.now() - timezone.timedelta(minutes=25)
        )

        if status == "Started":
            return

        # Pickup
        OrderEvent.objects.create(
            order=order,
            event="Pickup",
            description="Rider arrived at pickup location",
            created_at=timezone.now() - timezone.timedelta(minutes=20)
        )

        if status == "Pickup":
            return

        # Fulfilling
        OrderEvent.objects.create(
            order=order,
            event="Fulfilling",
            description="Rider picked up items and is in transit",
            created_at=timezone.now() - timezone.timedelta(minutes=15)
        )

        if status == "Fulfilling":
            return

        # Arrived
        OrderEvent.objects.create(
            order=order,
            event="Arrived",
            description="Rider arrived at delivery location",
            created_at=timezone.now() - timezone.timedelta(minutes=5)
        )

        if status == "Arrived":
            return

        # Done
        OrderEvent.objects.create(
            order=order,
            event="Done",
            description="Order delivered successfully",
            created_at=timezone.now() - timezone.timedelta(minutes=1)
        )
