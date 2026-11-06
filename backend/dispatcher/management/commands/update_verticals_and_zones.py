from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import Vertical, Zone


class Command(BaseCommand):
    help = "Updates zone-to-vertical assignments to match the March 2026 restructuring."

    def handle(self, *args, **options):
        # New zone arrangement per vertical
        new_arrangement = {
            "A": [
                {"name": "Osapa/Jakande", "lat": 6.4400, "lng": 3.5200, "desc": "Osapa, Jakande, Agungi"},
                {"name": "Awoyaya", "lat": 6.4833, "lng": 3.7000, "desc": "Awoyaya, Bogije, Lakowe, Ibeju axis"},
                {"name": "Ajah", "lat": 6.4667, "lng": 3.5667, "desc": "Ajah, Sangotedo, Ologolo, Agungi"},
                {"name": "Obalende", "lat": 6.4480, "lng": 3.4100, "desc": "Obalende, Lagos Island, Ikoyi, Victoria Island"},
            ],
            "B": [
                {"name": "Oshodi", "lat": 6.5142, "lng": 3.3087, "desc": "Oshodi, Isolo, Mushin, Mafoluku"},
                {"name": "Oyingbo", "lat": 6.4765, "lng": 3.3823, "desc": "Oyingbo, Lagos Island, Idumota, Marina"},
                {"name": "Tejuosho", "lat": 6.5061, "lng": 3.3665, "desc": "Tejuosho, Surulere, Ojuelegba, Itire"},
                {"name": "Sabo", "lat": 6.5062, "lng": 3.3782, "desc": "Sabo, Yaba, Abule Ijesha, Makoko"},
                {"name": "Bariga", "lat": 6.5350, "lng": 3.3947, "desc": "Bariga, Somolu, Gbagada, Pedro"},
            ],
            "C": [
                {"name": "Agege", "lat": 6.6198, "lng": 3.3222, "desc": "Agege, Oko Oba, Abule Egba, Ifako"},
                {"name": "Ikeja", "lat": 6.6059, "lng": 3.3491, "desc": "Ikeja, Computer Village, Allen, Oregun"},
                {"name": "Mile 12", "lat": 6.6063, "lng": 3.3954, "desc": "Mile 12, Owode, Alapere, Kosofe"},
                {"name": "Ikorodu", "lat": 6.6000, "lng": 3.5000, "desc": "Ikorodu, Benson, Igbogbo, Imota"},
                {"name": "Berger", "lat": 6.6470, "lng": 3.3742, "desc": "Berger, Ojota, Magodo, CMD Road"},
            ],
            "D": [
                {"name": "Ajegunle", "lat": 6.4520, "lng": 3.3312, "desc": "Ajegunle, Apapa, Kirikiri, Tolu"},
                {"name": "Festac", "lat": 6.4664, "lng": 3.2835, "desc": "Festac, 2nd Avenue, Amuwo Odofin"},
                {"name": "Iyana ipaja/egbeda", "lat": 6.5919, "lng": 3.2896, "desc": "Iyana Ipaja, Egbeda, Idimu, Isheri, Alimosho"},
                {"name": "Ikotun", "lat": 6.5531, "lng": 3.2697, "desc": "Ikotun, Igando, Ijegun, Satellite Town"},
                {"name": "Tradefair", "lat": 6.4650, "lng": 3.2600, "desc": "Trade Fair, Alaba International, ASPAMDA"},
                {"name": "Iyana Iba", "lat": 6.4606, "lng": 3.2036, "desc": "Iyana Iba, Iba, Ojo, Oloja"},
                {"name": "Ayobo", "lat": 6.6000, "lng": 3.2333, "desc": "Ayobo, Ipaja, Akowonjo, Meiran"},
            ],
        }

        # Zones to remove (no longer in the new arrangement)
        zones_to_remove = ["Lekki Phase 1", "Falomo"]

        # Zone rename mapping (old name -> new name)
        zones_to_rename = {
            "Egbeda": "Iyana ipaja/egbeda",
        }

        with transaction.atomic():
            # Fetch verticals
            verticals = {v.code: v for v in Vertical.objects.all()}
            if not verticals:
                self.stderr.write(self.style.ERROR("No verticals found. Run seed_verticals_and_zones first."))
                return

            # Step 1: Rename zones
            for old_name, new_name in zones_to_rename.items():
                updated = Zone.objects.filter(name=old_name).update(name=new_name)
                if updated:
                    self.stdout.write(self.style.WARNING(f"Renamed zone '{old_name}' -> '{new_name}'"))
                else:
                    self.stdout.write(f"Zone '{old_name}' not found for renaming (may not exist yet)")

            # Step 2: Deactivate removed zones
            for zone_name in zones_to_remove:
                updated = Zone.objects.filter(name=zone_name, is_active=True).update(is_active=False)
                if updated:
                    self.stdout.write(self.style.WARNING(f"Deactivated zone '{zone_name}'"))
                else:
                    self.stdout.write(f"Zone '{zone_name}' not found or already inactive")

            # Step 3: Create or update zones with correct vertical assignments
            for vertical_code, zones in new_arrangement.items():
                vertical = verticals.get(vertical_code)
                if not vertical:
                    self.stderr.write(self.style.ERROR(f"Vertical {vertical_code} not found, skipping"))
                    continue

                for z in zones:
                    zone, created = Zone.objects.update_or_create(
                        name=z["name"],
                        defaults={
                            "vertical": vertical,
                            "center_lat": z["lat"],
                            "center_lng": z["lng"],
                            "description": z["desc"],
                            "radius_km": 5.0,
                            "is_active": True,
                        },
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"Created zone '{z['name']}' in Vertical {vertical_code}"
                        ))
                    else:
                        self.stdout.write(
                            f"Updated zone '{z['name']}' -> Vertical {vertical_code}"
                        )

        self.stdout.write(self.style.SUCCESS("\nZone restructuring completed successfully!"))
