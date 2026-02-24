import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, Delivery, Vehicle
from riders.models import RiderEarning, RiderCodRecord
from dispatcher.models import Rider
from authentication.models import User
from decimal import Decimal


class Command(BaseCommand):
    help = "Populate completed orders for today for a specific rider using phone number"

    def add_arguments(self, parser):
        parser.add_argument("phone", type=str, help="Rider's phone number")
        parser.add_argument(
            "--count", type=int, default=5, help="Number of orders to create"
        )

    def handle(self, *args, **options):
        phone = options["phone"]
        count = options["count"]

        try:
            user = User.objects.get(phone=phone)
            # Try to get rider profile from the user
            rider = getattr(user, "rider_profile", None)
            if not rider:
                self.stdout.write(
                    self.style.ERROR(f"User with phone {phone} is not a rider.")
                )
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with phone {phone} not found."))
            return

        # Get or create a sample merchant
        merchant, _ = User.objects.get_or_create(
            phone="+2348111222333",
            defaults={
                "email": "mock_merchant@example.com",
                "business_name": "Mock Mart",
                "contact_name": "Mock Merchant",
                "usertype": "Merchant",
            },
        )

        # Get vehicle
        vehicle = rider.vehicle_type or Vehicle.objects.filter(is_active=True).first()
        if not vehicle:
            self.stdout.write(
                self.style.ERROR(
                    "No active vehicle found in the system. Use 'seed_vehicles' first."
                )
            )
            return

        now = timezone.now()

        locations = [
            ("Surulere", "V.I."),
            ("Ikeja", "Yaba"),
            ("Lekki", "Ajah"),
            ("Yaba", "Ikoyi"),
            ("Ikeja", "Surulere"),
            ("Maryland", "Oshodi"),
            ("Gbagada", "Lekki"),
            ("Mushin", "Apapa"),
            ("Ebutte Metta", "Lagos Island"),
        ]

        self.stdout.write(
            f"Populating {count} orders for {user.get_full_name()} ({rider.rider_id})..."
        )

        # Get the starting order number to avoid conflicts
        last_order = Order.objects.order_by("-order_number").first()
        try:
            current_num = int(last_order.order_number) if last_order else 6158000
        except ValueError:
            current_num = 6158000 + Order.objects.count()

        for i in range(count):
            current_num += 1
            pickup_area, dropoff_area = random.choice(locations)

            # Random time today between 8 AM and now
            start_of_day = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if now < start_of_day:
                start_of_day = now - timedelta(hours=4)

            seconds_diff = (now - start_of_day).total_seconds()
            random_seconds = random.randint(0, max(1, int(seconds_diff)))
            completed_time = start_of_day + timedelta(seconds=random_seconds)

            distance = Decimal(str(round(random.uniform(2.0, 15.0), 1)))
            # Simple mock pricing
            total_amount = Decimal(str(random.randint(1500, 4500)))
            earned = total_amount * Decimal("0.8")  # 80% to rider
            cod = Decimal(str(random.choice([0, 0, 5000, 8000, 15000, 20000])))

            order = Order.objects.create(
                order_number=str(current_num),
                user=merchant,
                rider=rider,
                vehicle=vehicle,
                status="Done",
                completed_at=completed_time,
                pickup_address=f"{pickup_area}, Lagos",
                sender_name="Mock Mart",
                sender_phone="+2348111222333",
                payment_method="cash" if cod > 0 else "wallet",
                payment_status="Paid",
                total_amount=total_amount,
                distance_km=distance,
                duration_minutes=random.randint(15, 60),
                created_at=completed_time - timedelta(minutes=random.randint(45, 120)),
            )

            Delivery.objects.create(
                order=order,
                dropoff_address=f"{dropoff_area}, Lagos",
                receiver_name=f"Customer {random.randint(100, 999)}",
                receiver_phone=f"+234800000{random.randint(1000, 9999)}",
                cod_amount=cod,
                status="Delivered",
                delivered_at=completed_time,
            )

            RiderEarning.objects.create(
                rider=rider,
                order=order,
                net_earning=earned,
                base_fare=total_amount * Decimal("0.4"),
                distance_fare=total_amount * Decimal("0.4"),
                commission_amount=total_amount * Decimal("0.2"),
                created_at=completed_time,
            )

            if cod > 0:
                RiderCodRecord.objects.create(
                    rider=rider,
                    order=order,
                    amount=cod,
                    status=RiderCodRecord.Status.PENDING,
                    created_at=completed_time,
                )

            self.stdout.write(
                f" - Created {order.order_number}: {pickup_area} -> {dropoff_area} | Earned: ₦{earned:,}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully populated {count} completed trips for today."
            )
        )
