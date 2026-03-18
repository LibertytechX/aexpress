import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from dispatcher.models import VehicleAsset, VehicleTracking
import string

class Command(BaseCommand):
    help = "Populate vehicle assets and vehicle tracking history"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting to populate vehicle assets..."))

        vehicle_types = [
            VehicleAsset.VehicleType.BIKE,
            VehicleAsset.VehicleType.CAR,
            VehicleAsset.VehicleType.VAN,
        ]

        makes = ['Honda', 'Toyota', 'Yamaha', 'Suzuki', 'Ford', 'TVS', 'Bajaj']
        colors = ['Red', 'Blue', 'Black', 'White', 'Silver']

        # Base coordinates somewhere in Lagos
        base_lat = 6.5244
        base_lng = 3.3792
        
        def random_plate():
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            nums = ''.join(random.choices(string.digits, k=4))
            end_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            return f"{letters}-{nums}-{end_letters}"

        # Create 10 assets
        for i in range(10):
            plate = random_plate()
            vtype = random.choice(vehicle_types)
            make = random.choice(makes)
            color = random.choice(colors)

            # Randomize start distance between 500 and 15000 km
            initial_distance = Decimal(str(round(random.uniform(500, 15000), 2)))

            asset, created = VehicleAsset.objects.get_or_create(
                plate_number=plate,
                defaults={
                    "vehicle_type": vtype,
                    "make": make,
                    "model": f"Model {random.randint(1, 5)}",
                    "year": random.randint(2015, 2023),
                    "color": color,
                    "engine_status": VehicleAsset.EngineStatus.ON,
                    "latitude": Decimal(str(round(base_lat + random.uniform(-0.05, 0.05), 7))),
                    "longitude": Decimal(str(round(base_lng + random.uniform(-0.05, 0.05), 7))),
                    "total_distance": initial_distance,
                    "unit_of_distance": "km",
                    "speed": Decimal(str(round(random.uniform(0, 60), 2))),
                    "is_active": True,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Vehicle Asset: {asset.asset_id} ({asset.plate_number})"))
            else:
                self.stdout.write(self.style.NOTICE(f"Asset {asset.plate_number} already exists. Populating tracking info..."))
                
            # Create tracking data for the past 3 days, every 2 hours
            self.stdout.write(f"Generating tracking history for {asset.asset_id}...")
            now = timezone.now()
            current_distance = asset.total_distance or initial_distance
            
            # Keep track of the last generated coordinates
            lat = asset.latitude or Decimal(str(base_lat))
            lng = asset.longitude or Decimal(str(base_lng))

            for days_ago in reversed(range(3)):
                for hour in range(0, 24, 2):
                    tracking_time = now - timedelta(days=days_ago, hours=hour)
                    
                    # Randomize lat/lng slightly to simulate movement
                    lat = Decimal(str(round(float(lat) + random.uniform(-0.01, 0.01), 7)))
                    lng = Decimal(str(round(float(lng) + random.uniform(-0.01, 0.01), 7)))
                    
                    # Increment distance slightly
                    current_distance += Decimal(str(round(random.uniform(1.0, 15.0), 2)))
                    
                    tracking = VehicleTracking(
                        vehicle_asset=asset,
                        latitude=lat,
                        longitude=lng,
                        travelled=current_distance,
                        unit_of_distance="km",
                    )
                    tracking.save()
                    
                    # Ensure created_at override
                    VehicleTracking.objects.filter(id=tracking.id).update(created_at=tracking_time)

            # Update final asset fields to match the last tracking info
            asset.total_distance = current_distance
            asset.latitude = lat
            asset.longitude = lng
            asset.last_telemetry_at = now
            asset.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated 10 vehicle assets with tracking history!'))
