from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import Zone, RelayNode

class Command(BaseCommand):
    help = "Populates Relay Nodes matching the provided spreadsheet."

    def handle(self, *args, **options):
        nodes_data = [
            # Island & Lekki Corridor
            {"name": "Osapa/Jakande", "address": "Triangle Mall, F039, Jakande", "lead": "DENNIS", "phone": "07039397708", "zone": "Island & Lekki Corridor", "lat": 6.4400, "lng": 3.5200},
            {"name": "Awoyaya", "address": "Beside Central Mosque, United Estate Busstop, Sangotedo", "lead": "DENNIS", "phone": "07049397708", "zone": "Island & Lekki Corridor", "lat": 6.4833, "lng": 3.7000},
            {"name": "Ajah", "address": "Building 2, First Floor View Point Plaza, Nepa Rd, Ajah Lagos", "lead": "DENNIS", "phone": "07059397708", "zone": "Island & Lekki Corridor", "lat": 6.4667, "lng": 3.5667},
            {"name": "Obalende", "address": "Behind Nipost Office, Obalende", "lead": "DENNIS", "phone": "07039397708", "zone": "Island & Lekki Corridor", "lat": 6.4480, "lng": 3.4100},
            
            # Central Mainland
            {"name": "Oshodi", "address": "Terminal 3, Above Lions Bite, Oshodi", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.5142, "lng": 3.3087},
            {"name": "Oyingbo", "address": "Shop 36, Second Floor Ultramodern Plaza, Oyingbo Market", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.4765, "lng": 3.3823},
            {"name": "Tejuosho", "address": "17, Tejuosho Rd, Yaba Lagos", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.5061, "lng": 3.3665},
            {"name": "Sabo", "address": "Sabo Modern Plaza,Shop 320, Block 10, Sabo", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.5062, "lng": 3.3782},
            {"name": "Bariga", "address": "27, Shop 26, Jagunmola Street, Off Bariga Mkt", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.5350, "lng": 3.3947},
            {"name": "Ajegunle", "address": "Shop 92, Alayabiagba Complex, Ajegunle Boundary.", "lead": "ESTHER", "phone": "08024018062", "zone": "Central Mainland", "lat": 6.4520, "lng": 3.3312},
            
            # Southwest Mainland
            {"name": "Festac", "address": "Shop L9, 402 Rd By 23rd Market, Directly Opposite C Close 402", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.4664, "lng": 3.2835},
            {"name": "Iyana ipaja/egbeda", "address": "Shop C3, Rosh Jidam Complex Beside Masaku Palace.", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.5919, "lng": 3.2896},
            {"name": "Ikotun", "address": "Alhaja Busstop Front Of The Bldg Beside Bovasfilling Station", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.5531, "lng": 3.2697},
            {"name": "Tradefair", "address": "Shop 50, New Jerusalem Mall,opposite Balogun", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.4650, "lng": 3.2600},
            {"name": "Iyana Iba", "address": "25, Praise Plaza Ikotun Igando Rd, Opposite Fidelity Bank Igando", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.4606, "lng": 3.2036},
            {"name": "Ayobo", "address": "32, Ayobo Market, Near Ishefun Rd, By Megida, Ayobo Lagos", "lead": "IBRAHIM", "phone": "08094601017", "zone": "Southwest Mainland", "lat": 6.6000, "lng": 3.2333},
            
            # North & Ikorodu
            {"name": "Agege", "address": "Abimbola Plaza, Opposite Ap Market, Agege, Lagos", "lead": "MARY", "phone": "07037561392", "zone": "North & Ikorodu", "lat": 6.6198, "lng": 3.3222},
            {"name": "Ikeja", "address": "18, Medical Rd, Nearjara Mall, Off Computer Village", "lead": "MARY", "phone": "07037561392", "zone": "North & Ikorodu", "lat": 6.6059, "lng": 3.3491},
            {"name": "Mile 12", "address": "619, Adeniji Plaza, Ikorodu Rd, Mile 12 Underbridge", "lead": "MARY", "phone": "07037561392", "zone": "North & Ikorodu", "lat": 6.6063, "lng": 3.3954},
            {"name": "Ikorodu", "address": "1, Alhaji Alagogo Street, Off Ayangburen Rd, Ikorodu, Lagos", "lead": "MARY", "phone": "07037561392", "zone": "North & Ikorodu", "lat": 6.6000, "lng": 3.5000},
            {"name": "Berger", "address": "16, Kosoko Street, Berger, Lagos", "lead": "MARY", "phone": "07037561392", "zone": "North & Ikorodu", "lat": 6.6470, "lng": 3.3742},
        ]

        with transaction.atomic():
            for data in nodes_data:
                zone_name = data["zone"]
                zone = Zone.objects.filter(name__iexact=zone_name).first()
                if not zone:
                    self.stderr.write(self.style.ERROR(f"Zone '{zone_name}' not found. Skipping relay node creation for {data['name']}."))
                    continue
                
                relay_node_name = data["name"]

                node, created = RelayNode.objects.update_or_create(
                    name=relay_node_name,
                    zone=zone,
                    defaults={
                        "address": data["address"],
                        "latitude": data["lat"],
                        "longitude": data["lng"],
                        "hub_captain_name": data["lead"],
                        "hub_captain_phone": data["phone"],
                        "is_active": True,
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Relay Node: {relay_node_name} for Zone '{zone.name}'"))
                else:
                    self.stdout.write(f"Updated Relay Node: {relay_node_name} for Zone '{zone.name}'")

        self.stdout.write(self.style.SUCCESS("\nRelay nodes population completed successfully!"))
