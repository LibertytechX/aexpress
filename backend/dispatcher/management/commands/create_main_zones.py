from django.core.management.base import BaseCommand
from dispatcher.models import Zone, Vertical

class Command(BaseCommand):
    help = "Creates the primary regional zones."

    def handle(self, *args, **options):
        # The user requested zones for:
        # North & Ikorodu
        # Southwest Mainland
        # Island & Lekki Corridor
        # Central Mainland
        
        zones_data = [
            {
                "name": "North & Ikorodu",
                "lat": 6.6000,
                "lng": 3.5000,
                "desc": "Primary regional zone for North & Ikorodu.",
            },
            {
                "name": "Southwest Mainland",
                "lat": 6.4664,
                "lng": 3.2835,
                "desc": "Primary regional zone for Southwest Mainland.",
            },
            {
                "name": "Island & Lekki Corridor",
                "lat": 6.4531,
                "lng": 3.3958,
                "desc": "Primary regional zone for Island & Lekki Corridor.",
            },
            {
                "name": "Central Mainland",
                "lat": 6.5061,
                "lng": 3.3665,
                "desc": "Primary regional zone for Central Mainland.",
            },
        ]

        for z in zones_data:
            zone, created = Zone.objects.update_or_create(
                name=z["name"],
                defaults={
                    "vertical": None,  # Zone as an independent entity
                    "center_lat": z["lat"],
                    "center_lng": z["lng"],
                    "description": z["desc"],
                    "radius_km": 10.0,  # Larger radius for regional zones
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Zone: {z['name']}"))
            else:
                self.stdout.write(f"Updated Zone: {z['name']}")

        self.stdout.write(self.style.SUCCESS("Successfully created/updated all main zones!"))
