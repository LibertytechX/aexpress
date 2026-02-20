from django.core.management.base import BaseCommand
from orders.models import Vehicle


class Command(BaseCommand):
    help = "Seed initial vehicle data"

    def handle(self, *args, **kwargs):
        """Create initial vehicle types with pricing."""

        vehicles_data = [
            {
                "name": "Bike",
                "max_weight_kg": 10,
                "base_price": 1000.00,  # Legacy field (deprecated)
                "base_fare": 500.00,  # Base fare for any delivery
                "rate_per_km": 50.00,  # ₦50 per kilometer
                "rate_per_minute": 10.00,  # ₦10 per minute
                "description": "Motorcycle delivery for small packages up to 10kg",
                "is_active": True,
            },
            {
                "name": "Car",
                "max_weight_kg": 70,
                "base_price": 2000.00,  # Legacy field (deprecated)
                "base_fare": 1000.00,  # Base fare for any delivery
                "rate_per_km": 100.00,  # ₦100 per kilometer
                "rate_per_minute": 20.00,  # ₦20 per minute
                "description": "Car delivery for medium packages up to 70kg",
                "is_active": True,
            },
            {
                "name": "Van",
                "max_weight_kg": 600,
                "base_price": 5000.00,  # Legacy field (deprecated)
                "base_fare": 2000.00,  # Base fare for any delivery
                "rate_per_km": 200.00,  # ₦200 per kilometer
                "rate_per_minute": 40.00,  # ₦40 per minute
                "description": "Van delivery for large packages up to 600kg",
                "is_active": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for vehicle_data in vehicles_data:
            vehicle, created = Vehicle.objects.update_or_create(
                name=vehicle_data["name"],
                defaults={
                    "max_weight_kg": vehicle_data["max_weight_kg"],
                    "base_price": vehicle_data["base_price"],
                    "base_fare": vehicle_data["base_fare"],
                    "rate_per_km": vehicle_data["rate_per_km"],
                    "rate_per_minute": vehicle_data["rate_per_minute"],
                    "description": vehicle_data["description"],
                    "is_active": vehicle_data["is_active"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created vehicle: {vehicle.name} - Base: ₦{vehicle.base_fare} + ₦{vehicle.rate_per_km}/km + ₦{vehicle.rate_per_minute}/min"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"↻ Updated vehicle: {vehicle.name} - Base: ₦{vehicle.base_fare} + ₦{vehicle.rate_per_km}/km + ₦{vehicle.rate_per_minute}/min"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seeding complete! Created: {created_count}, Updated: {updated_count}"
            )
        )
