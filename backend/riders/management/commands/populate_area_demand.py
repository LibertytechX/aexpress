from django.core.management.base import BaseCommand
from riders.models import AreaDemand
import uuid


class Command(BaseCommand):
    help = "Populate initial AreaDemand data"

    def handle(self, *args, **options):
        areas = [
            {
                "area_name": "Ikeja",
                "latitude": 6.6018,
                "longitude": 3.3515,
                "level": AreaDemand.Level.HIGH,
            },
            {
                "area_name": "Yaba",
                "latitude": 6.5095,
                "longitude": 3.3711,
                "level": AreaDemand.Level.MEDIUM,
            },
            {
                "area_name": "VI",
                "latitude": 6.4311,
                "longitude": 3.4158,
                "level": AreaDemand.Level.HIGH,
            },
            {
                "area_name": "Lekki",
                "latitude": 6.4584,
                "longitude": 3.6015,
                "level": AreaDemand.Level.MEDIUM,
            },
        ]

        for area_data in areas:
            area, created = AreaDemand.objects.update_or_create(
                area_name=area_data["area_name"],
                defaults={
                    "latitude": area_data["latitude"],
                    "longitude": area_data["longitude"],
                    "level": area_data["level"],
                    "pending_orders": (
                        10 if area_data["level"] == AreaDemand.Level.HIGH else 5
                    ),
                    "active_riders": (
                        5 if area_data["level"] == AreaDemand.Level.HIGH else 2
                    ),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created area: {area.area_name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated area: {area.area_name}"))
