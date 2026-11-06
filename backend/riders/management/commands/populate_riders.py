import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dispatcher.models import Rider, VehicleAsset

User = get_user_model()


class Command(BaseCommand):
    help = "Generate sample riders and their corresponding user accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of riders to create (default 50)",
        )

    def handle(self, *args, **options):
        count = options["count"]

        first_names = [
            "Emeka",
            "Chukwudi",
            "Adesola",
            "Musa",
            "Tunde",
            "Yetunde",
            "Chidi",
            "Fatima",
            "Obinna",
            "Seun",
            "Aminu",
            "Taiwo",
            "Nkechi",
            "Bashir",
            "Chiamaka",
            "Dayo",
            "Kola",
            "Halima",
            "Ifeanyi",
            "Zainab",
            "Uche",
            "Sade",
            "Adamu",
            "Tobi",
            "Ngozi",
            "Saheed",
            "Chisom",
            "Yakubu",
            "Rotimi",
            "Aisha",
            "Olu",
            "Ifeoma",
            "Kabiru",
            "Funke",
            "Chibuzor",
            "Hajiya",
            "Lanre",
            "Adaeze",
            "Garba",
            "Titi",
        ]
        last_names = [
            "Okafor",
            "Eze",
            "Bello",
            "Ibrahim",
            "Fashola",
            "Adeyemi",
            "Nwosu",
            "Aliyu",
            "Ogbu",
            "Akinwale",
            "Garba",
            "Oladele",
            "Obi",
            "Umar",
            "Eze",
            "Adeleke",
            "Afolabi",
            "Sani",
            "Okeke",
            "Mohammed",
            "Nwachukwu",
            "Coker",
            "Bala",
            "Lawson",
            "Asika",
            "Lawal",
            "Agu",
            "Danladi",
            "Osoba",
            "Kabir",
            "Martins",
            "Nweze",
            "Shehu",
            "Olanrewaju",
            "Onuoha",
            "Musa",
            "Badmus",
            "Okonkwo",
            "Abdullahi",
            "Olawale",
        ]

        # Get some vehicle assets to assign to riders (optional, but good for testing)
        vehicles = list(VehicleAsset.objects.all())

        created_count = 0

        # Start phone numbers from a high offset to avoid collisions with other scripts
        phone_start = 900000000

        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            phone = f"+23481{phone_start + i}"
            email = f"rider_{phone_start + i}@example.com"

            if User.objects.filter(phone=phone).exists():
                continue

            # Create User
            user = User.objects.create_user(
                phone=phone,
                email=email,
                password="password123",  # Default test password
                usertype="Rider",
                first_name=first_name,
                last_name=last_name,
                contact_name=f"{first_name} {last_name}",
            )

            # Update auto-created Rider Profile
            rider = Rider.objects.get(user=user)
            rider.is_authorized = True
            rider.is_registration_verified = True
            rider.status = Rider.Status.OFFLINE
            if vehicles:
                rider.vehicle_asset = random.choice(vehicles)
            rider.save()

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} riders and user accounts."
            )
        )
