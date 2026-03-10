import random
import string
from django.core.management.base import BaseCommand
from dispatcher.models import VehicleAsset


class Command(BaseCommand):
    help = "Generate sample vehicle assets for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of vehicle assets to create (default 50)",
        )

    def handle(self, *args, **options):
        count = options["count"]

        vehicle_types = [
            VehicleAsset.VehicleType.BIKE,
            VehicleAsset.VehicleType.CAR,
            VehicleAsset.VehicleType.VAN,
        ]
        makes_models = {
            VehicleAsset.VehicleType.BIKE: [
                ("Honda", "Ace 125"),
                ("Bajaj", "Boxer"),
                ("TVS", "HLX 125"),
            ],
            VehicleAsset.VehicleType.CAR: [
                ("Toyota", "Corolla"),
                ("Honda", "Civic"),
                ("Hyundai", "Elantra"),
            ],
            VehicleAsset.VehicleType.VAN: [
                ("Ford", "Transit"),
                ("Toyota", "Hiace"),
                ("Mercedes-Benz", "Sprinter"),
            ],
        }
        colors = ["Red", "Blue", "Black", "White", "Silver", "Yellow"]

        created_count = 0

        for i in range(count):
            v_type = random.choice(vehicle_types)
            make, model = random.choice(makes_models[v_type])
            color = random.choice(colors)
            year = random.randint(2015, 2024)

            # Generate a random plate number, e.g., KJA-123XC
            letters = "".join(random.choices(string.ascii_uppercase, k=3))
            digits = "".join(random.choices(string.digits, k=3))
            suffix = "".join(random.choices(string.ascii_uppercase, k=2))
            plate_number = f"{letters}-{digits}{suffix}"

            if VehicleAsset.objects.filter(plate_number=plate_number).exists():
                continue

            VehicleAsset.objects.create(
                plate_number=plate_number,
                vehicle_type=v_type,
                make=make,
                model=model,
                year=year,
                color=color,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} vehicle assets.")
        )
