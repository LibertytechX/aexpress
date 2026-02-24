from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from orders.models import Order, Delivery, Vehicle
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Populate mock orders with cash and wallet payment methods"

    def handle(self, *args, **options):
        self.stdout.write("Populating mock orders...")

        try:
            with transaction.atomic():
                # 1. Get or create a sample merchant
                merchant, _ = User.objects.get_or_create(
                    phone="+2348111222333",
                    defaults={
                        "email": "mock_merchant@example.com",
                        "business_name": "Mock Mart",
                        "contact_name": "Mock Merchant",
                        "usertype": "Merchant",
                    },
                )

                # 2. Get or create a sample vehicle
                vehicle, _ = Vehicle.objects.get_or_create(
                    name="Mock Bike",
                    defaults={
                        "max_weight_kg": 50,
                        "base_price": 500,
                        "base_fare": 500,
                        "rate_per_km": 50,
                        "rate_per_minute": 5,
                        "min_distance_km": 2,
                        "min_fee": 600,
                    },
                )

                # 3. Create 5 Cash orders (Pending)
                for i in range(5):
                    self.create_order(
                        user=merchant,
                        vehicle=vehicle,
                        payment_method="cash",
                        payment_status="Pending",
                        total_amount=Decimal("1200.00"),
                        index=i + 1,
                    )

                # 4. Create 5 Wallet orders (Paid)
                for i in range(5):
                    self.create_order(
                        user=merchant,
                        vehicle=vehicle,
                        payment_method="wallet",
                        payment_status="Paid",
                        total_amount=Decimal("1500.00"),
                        index=i + 6,
                    )

            self.stdout.write(
                self.style.SUCCESS("Successfully populated 10 mock orders.")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            import traceback

            self.stdout.write(traceback.format_exc())

    def create_order(
        self, user, vehicle, payment_method, payment_status, total_amount, index
    ):
        """Helper to create an order and its delivery."""
        order = Order.objects.create(
            user=user,
            mode="quick",
            status="Pending",
            vehicle=vehicle,
            pickup_address=f"{100 + index} Mock Street, Ikeja, Lagos",
            sender_name="Mock Mart",
            sender_phone="+2348111222333",
            payment_method=payment_method,
            payment_status=payment_status,
            total_amount=total_amount,
            distance_km=Decimal(f"{3.5 + index/10}"),
            duration_minutes=15 + index,
        )

        Delivery.objects.create(
            order=order,
            dropoff_address=f"{200 + index} Delivery Road, Lekki, Lagos",
            receiver_name=f"Receiver {index}",
            receiver_phone=f"+234800000000{index}",
            package_type="Box",
        )
        self.stdout.write(
            f"Created order {order.order_number}: {payment_method} - {payment_status}"
        )
