from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from dispatcher.models import Rider, Merchant
from orders.models import Vehicle

User = get_user_model()


class Command(BaseCommand):
    help = "Populate initial data for Riders and Merchants"

    def handle(self, *args, **kwargs):
        self.stdout.write("Populating data...")

        try:
            with transaction.atomic():
                self.create_merchants()
                self.create_riders()
                self.stdout.write(self.style.SUCCESS("Users populated successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error populating data: {e}"))

    def create_merchants(self):
        merchants_data = [
            {
                "phone": "+2348011111111",
                "email": "merchant.one@example.com",
                "password": "password123",
                "business_name": "Tasty Meals",
                "contact_name": "Chioma Adebayo",
                "address": "123 Allen Avenue, Ikeja",
            },
            {
                "phone": "+2348022222222",
                "email": "merchant.two@example.com",
                "password": "password123",
                "business_name": "Gadget World",
                "contact_name": "Emeka Nnamdi",
                "address": "45 Computer Village, Ikeja",
            },
        ]

        count = 0
        for data in merchants_data:
            if not User.objects.filter(phone=data["phone"]).exists():
                user = User.objects.create_user(
                    phone=data["phone"],
                    email=data["email"],
                    password=data["password"],
                    business_name=data["business_name"],
                    contact_name=data["contact_name"],
                    address=data["address"],
                    usertype="Merchant",
                )
                # Merchant profile created via signal
                count += 1
                self.stdout.write(f"✓ Created merchant: {data['business_name']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Merchant exists: {data['business_name']}")
                )

        self.stdout.write(self.style.SUCCESS(f"Created {count} new merchants"))

    def create_riders(self):
        riders_data = [
            {
                "phone": "+2348033333333",
                "email": "rider.one@example.com",
                "password": "password123",
                "contact_name": "Musa Ibrahim",
                "vehicle": "Bike",
                "status": "online",
            },
            {
                "phone": "+2348044444444",
                "email": "rider.two@example.com",
                "password": "password123",
                "contact_name": "John Doe",
                "vehicle": "Car",
                "status": "online",
            },
            {
                "phone": "+2348055555555",
                "email": "rider.three@example.com",
                "password": "password123",
                "contact_name": "Alice Smith",
                "vehicle": "Van",
                "status": "offline",
            },
        ]

        count = 0
        for data in riders_data:
            if not User.objects.filter(phone=data["phone"]).exists():
                user = User.objects.create_user(
                    phone=data["phone"],
                    email=data["email"],
                    password=data["password"],
                    contact_name=data["contact_name"],
                    usertype="Rider",
                )

                # Rider profile created via signal, fetch and update
                rider = Rider.objects.get(user=user)

                vehicle_type = Vehicle.objects.filter(
                    name__iexact=data["vehicle"]
                ).first()
                if not vehicle_type:
                    vehicle_type = Vehicle.objects.first()

                rider.vehicle_type = vehicle_type
                rider.status = data.get("status", "offline")
                rider.save()

                count += 1
                self.stdout.write(f"✓ Created rider: {data['contact_name']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Rider exists: {data['contact_name']}")
                )

        self.stdout.write(self.style.SUCCESS(f"Created {count} new riders"))
