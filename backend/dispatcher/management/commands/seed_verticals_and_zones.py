import uuid
from django.core.management.base import BaseCommand
from dispatcher.models import Vertical, Zone

class Command(BaseCommand):
    help = "Seeds the 4 AXpress Verticals and 20 Lagos Zones with coordinates and leads."

    def handle(self, *args, **options):
        # 1. Define Verticals
        verticals_data = [
            {"code": "A", "name": "Island & Lekki Corridor", "lead": "Dennis"},
            {"code": "B", "name": "Central Mainland", "lead": "Seun"},
            {"code": "C", "name": "North & Ikorodu", "lead": "Mary"},
            {"code": "D", "name": "Southwest Mainland", "lead": "Erinfolami"},
        ]

        vertical_objs = {}
        for v in verticals_data:
            obj, created = Vertical.objects.get_or_create(
                code=v["code"],
                defaults={
                    "name": v["name"],
                    "lead_name": v["lead"],
                }
            )
            vertical_objs[v["code"]] = obj
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Vertical {v['code']}"))
            else:
                self.stdout.write(f"Vertical {v['code']} already exists")

        # 2. Define Zones Mapping
        zones_data = [
            # Vertical A
            {"v": "A", "name": "Awoyaya", "lat": 6.4833, "lng": 3.7000, "desc": "Awoyaya, Bogije, Lakowe, Ibeju axis"},
            {"v": "A", "name": "Ajah", "lat": 6.4667, "lng": 3.5667, "desc": "Ajah, Sangotedo, Ologolo, Agungi"},
            {"v": "A", "name": "Lekki Phase 1", "lat": 6.4531, "lng": 3.3958, "desc": "Lekki Ph1, Oniru, Ikate, Chevron"},
            {"v": "A", "name": "Falomo", "lat": 6.4439, "lng": 3.4270, "desc": "Falomo, Ikoyi, Victoria Island"},
            {"v": "A", "name": "Oyingbo", "lat": 6.4765, "lng": 3.3823, "desc": "Oyingbo, Lagos Island, Idumota, Marina"},
            # Vertical B
            {"v": "B", "name": "Sabo", "lat": 6.5062, "lng": 3.3782, "desc": "Sabo, Yaba, Abule Ijesha, Makoko"},
            {"v": "B", "name": "Tejuosho", "lat": 6.5061, "lng": 3.3665, "desc": "Tejuosho, Surulere, Ojuelegba, Itire"},
            {"v": "B", "name": "Bariga", "lat": 6.5350, "lng": 3.3947, "desc": "Bariga, Somolu, Gbagada, Pedro"},
            {"v": "B", "name": "Oshodi", "lat": 6.5142, "lng": 3.3087, "desc": "Oshodi, Isolo, Mushin, Mafoluku"},
            {"v": "B", "name": "Mile 12", "lat": 6.6063, "lng": 3.3954, "desc": "Mile 12, Owode, Alapere, Kosofe"},
            # Vertical C
            {"v": "C", "name": "Ikeja", "lat": 6.6059, "lng": 3.3491, "desc": "Ikeja, Computer Village, Allen, Oregun"},
            {"v": "C", "name": "Ikorodu", "lat": 6.6000, "lng": 3.5000, "desc": "Ikorodu, Benson, Igbogbo, Imota"},
            {"v": "C", "name": "Berger", "lat": 6.6470, "lng": 3.3742, "desc": "Berger, Ojota, Magodo, CMD Road"},
            {"v": "C", "name": "Agege", "lat": 6.6198, "lng": 3.3222, "desc": "Agege, Oko Oba, Abule Egba, Ifako"},
            {"v": "C", "name": "Ayobo", "lat": 6.6000, "lng": 3.2333, "desc": "Ayobo, Ipaja, Akowonjo, Meiran"},
            # Vertical D
            {"v": "D", "name": "Egbeda", "lat": 6.5919, "lng": 3.2896, "desc": "Egbeda, Idimu, Isheri, Alimosho"},
            {"v": "D", "name": "Ikotun", "lat": 6.5531, "lng": 3.2697, "desc": "Ikotun, Igando, Ijegun, Satellite Town"},
            {"v": "D", "name": "Iyana Iba", "lat": 6.4606, "lng": 3.2036, "desc": "Iyana Iba, Iba, Ojo, Oloja"},
            {"v": "D", "name": "Festac", "lat": 6.4664, "lng": 3.2835, "desc": "Festac, 2nd Avenue, Amuwo Odofin"},
            {"v": "D", "name": "Ajegunle", "lat": 6.4520, "lng": 3.3312, "desc": "Ajegunle, Apapa, Kirikiri, Tolu"},
        ]

        for z in zones_data:
            obj, created = Zone.objects.update_or_create(
                name=z["name"],
                defaults={
                    "vertical": vertical_objs[z["v"]],
                    "center_lat": z["lat"],
                    "center_lng": z["lng"],
                    "description": z["desc"],
                    "radius_km": 5.0, # Default radius
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Zone {z['name']} in Vertical {z['v']}"))
            else:
                self.stdout.write(f"Updated Zone {z['name']} in Vertical {z['v']}")

        self.stdout.write(self.style.SUCCESS("AXpress Seeding Completed Successfully!"))
