"""
Management command to seed Lagos relay network with 20 nodes and 2 riders per node.
Usage: python manage.py seed_relay_network [--clear]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import Zone, RelayNode, Rider
from authentication.models import User
from orders.models import Vehicle

ZONES = [
    {
        "name": "Lagos Island / Victoria Island",
        "center_lat": 6.4550,
        "center_lng": 3.4050,
        "radius_km": 6.0,
    },
    {
        "name": "Lekki / Ajah Corridor",
        "center_lat": 6.4520,
        "center_lng": 3.5700,
        "radius_km": 12.0,
    },
    {
        "name": "Ikeja / Mainland North",
        "center_lat": 6.6000,
        "center_lng": 3.3500,
        "radius_km": 8.0,
    },
    {
        "name": "Yaba / Surulere",
        "center_lat": 6.5050,
        "center_lng": 3.3700,
        "radius_km": 6.0,
    },
    {
        "name": "Apapa / Festac / Ojo",
        "center_lat": 6.4700,
        "center_lng": 3.2950,
        "radius_km": 8.0,
    },
]

# 20 relay nodes (zone_key references ZONES list index)
RELAY_NODES = [
    # Lagos Island / VI (zone 0)
    {"name": "Tafawa Balewa Square", "address": "Tafawa Balewa Square, Lagos Island, Lagos", "lat": 6.4514, "lng": 3.3916, "zone": 0},
    {"name": "CMS Marina", "address": "CMS Marina, Lagos Island, Lagos", "lat": 6.4550, "lng": 3.3914, "zone": 0},
    {"name": "Victoria Island – Adeola Odeku", "address": "Adeola Odeku Street, Victoria Island, Lagos", "lat": 6.4281, "lng": 3.4219, "zone": 0},
    {"name": "Ikoyi – Awolowo Road", "address": "Awolowo Road, Ikoyi, Lagos", "lat": 6.4451, "lng": 3.4302, "zone": 0},
    {"name": "Oniru / Maroko", "address": "Oniru, Victoria Island Extension, Lagos", "lat": 6.4352, "lng": 3.4548, "zone": 0},
    # Lekki / Ajah (zone 1)
    {"name": "Lekki Phase 1 – Chevron Drive", "address": "Chevron Drive, Lekki Phase 1, Lagos", "lat": 6.4383, "lng": 3.5212, "zone": 1},
    {"name": "Lekki Phase 2 – Abraham Adesanya", "address": "Abraham Adesanya Estate, Lekki Phase 2, Lagos", "lat": 6.4677, "lng": 3.5664, "zone": 1},
    {"name": "Ajah Roundabout", "address": "Ajah Roundabout, Lekki-Epe Expressway, Lagos", "lat": 6.4697, "lng": 3.6019, "zone": 1},
    {"name": "Sangotedo – Novare Mall", "address": "Novare Mall, Sangotedo, Lagos", "lat": 6.4507, "lng": 3.6158, "zone": 1},
    # Ikeja / Mainland North (zone 2)
    {"name": "Ikeja – Allen Avenue", "address": "Allen Avenue, Ikeja, Lagos", "lat": 6.6018, "lng": 3.3515, "zone": 2},
    {"name": "Alausa Secretariat", "address": "Alausa Secretariat, Ikeja, Lagos", "lat": 6.5846, "lng": 3.3496, "zone": 2},
    {"name": "Ojodu Berger Junction", "address": "Ojodu Berger Bus Stop, Lagos", "lat": 6.6285, "lng": 3.3676, "zone": 2},
    {"name": "Ogba Roundabout", "address": "Ogba Roundabout, Ogba, Lagos", "lat": 6.6136, "lng": 3.3220, "zone": 2},
    # Yaba / Surulere (zone 3)
    {"name": "Yaba – Herbert Macaulay Way", "address": "Herbert Macaulay Way, Yaba, Lagos", "lat": 6.5063, "lng": 3.3781, "zone": 3},
    {"name": "Surulere – Adeniran Ogunsanya", "address": "Adeniran Ogunsanya Street, Surulere, Lagos", "lat": 6.4987, "lng": 3.3511, "zone": 3},
    {"name": "Mushin Roundabout", "address": "Mushin Roundabout, Mushin, Lagos", "lat": 6.5342, "lng": 3.3577, "zone": 3},
    {"name": "Costain Roundabout", "address": "Costain Roundabout, Lagos", "lat": 6.4811, "lng": 3.3681, "zone": 3},
    # Apapa / Festac / Ojo (zone 4)
    {"name": "Apapa Wharf", "address": "Apapa Wharf Gate, Apapa, Lagos", "lat": 6.4500, "lng": 3.3610, "zone": 4},
    {"name": "Festac Town Phase 1", "address": "4th Avenue, Festac Town, Lagos", "lat": 6.4657, "lng": 3.2842, "zone": 4},
    {"name": "Mile 2 Roundabout", "address": "Mile 2 Roundabout, Lagos", "lat": 6.4767, "lng": 3.3115, "zone": 4},
]

# Nigerian names for riders
RIDER_NAMES = [
    ("Emeka", "Okafor"), ("Chukwudi", "Eze"), ("Adesola", "Bello"), ("Musa", "Ibrahim"),
    ("Tunde", "Fashola"), ("Yetunde", "Adeyemi"), ("Chidi", "Nwosu"), ("Fatima", "Aliyu"),
    ("Obinna", "Ogbu"), ("Seun", "Akinwale"), ("Aminu", "Garba"), ("Taiwo", "Oladele"),
    ("Nkechi", "Obi"), ("Bashir", "Umar"), ("Chiamaka", "Eze"), ("Dayo", "Adeleke"),
    ("Kola", "Afolabi"), ("Halima", "Sani"), ("Ifeanyi", "Okeke"), ("Zainab", "Mohammed"),
    ("Uche", "Nwachukwu"), ("Sade", "Coker"), ("Adamu", "Bala"), ("Tobi", "Lawson"),
    ("Ngozi", "Asika"), ("Saheed", "Lawal"), ("Chisom", "Agu"), ("Yakubu", "Danladi"),
    ("Rotimi", "Osoba"), ("Aisha", "Kabir"), ("Olu", "Martins"), ("Ifeoma", "Nweze"),
    ("Kabiru", "Shehu"), ("Funke", "Olanrewaju"), ("Chibuzor", "Onuoha"), ("Hajiya", "Musa"),
    ("Lanre", "Badmus"), ("Adaeze", "Okonkwo"), ("Garba", "Abdullahi"), ("Titi", "Olawale"),
]


class Command(BaseCommand):
    help = "Seed Lagos relay network with 20 nodes and 2 riders per node (40 riders)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing relay nodes/zones before seeding (riders are NOT deleted)",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["clear"]:
                RelayNode.objects.all().delete()
                Zone.objects.all().delete()
                self.stdout.write(self.style.WARNING("⚠  Cleared existing zones and relay nodes."))

            zone_objs = self._create_zones()
            node_objs = self._create_nodes(zone_objs)
            self._create_riders(node_objs, zone_objs)

        self.stdout.write(self.style.SUCCESS("\n✅  Relay network seeding complete!"))
        self.stdout.write(f"   Zones:       {len(zone_objs)}")
        self.stdout.write(f"   Relay nodes: {len(node_objs)}")
        self.stdout.write(f"   Riders:      up to {len(node_objs) * 2} (skips existing phones)")

    # ------------------------------------------------------------------
    def _create_zones(self):
        zone_objs = []
        for z in ZONES:
            obj, created = Zone.objects.get_or_create(
                name=z["name"],
                defaults={
                    "center_lat": z["center_lat"],
                    "center_lng": z["center_lng"],
                    "radius_km": z["radius_km"],
                    "is_active": True,
                },
            )
            zone_objs.append(obj)
            mark = "✓ created" if created else "· exists"
            self.stdout.write(f"  Zone {mark}: {obj.name}")
        return zone_objs

    def _create_nodes(self, zone_objs):
        node_objs = []
        for n in RELAY_NODES:
            zone = zone_objs[n["zone"]]
            obj, created = RelayNode.objects.get_or_create(
                name=n["name"],
                defaults={
                    "address": n["address"],
                    "latitude": n["lat"],
                    "longitude": n["lng"],
                    "zone": zone,
                    "catchment_radius_km": 2.0,
                    "is_active": True,
                },
            )
            node_objs.append(obj)
            mark = "✓ created" if created else "· exists"
            self.stdout.write(f"  Node {mark}: {obj.name} [{zone.name}]")
        return node_objs

    def _create_riders(self, node_objs, zone_objs):
        # Get or create a Bike vehicle type for the riders
        bike, _ = Vehicle.objects.get_or_create(
            name="Bike",
            defaults={"max_weight_kg": 30, "base_price": 500, "base_fare": 500},
        )

        rider_index = 0
        for node in node_objs:
            for slot in range(2):  # 2 riders per node
                first, last = RIDER_NAMES[rider_index % len(RIDER_NAMES)]
                rider_index += 1
                phone = f"+234801{rider_index:06d}"
                email = f"relay.rider.{rider_index}@axpress.ng"
                contact_name = f"{first} {last}"

                if User.objects.filter(phone=phone).exists():
                    self.stdout.write(f"  Rider · exists: {contact_name} ({phone})")
                    continue

                user = User.objects.create_user(
                    phone=phone,
                    email=email,
                    password="Relay@2026",
                    contact_name=contact_name,
                    business_name=f"Relay Rider {rider_index}",
                    usertype="Rider",
                )

                # Rider profile may be created via signal; use get_or_create to be safe
                rider, _ = Rider.objects.get_or_create(
                    user=user,
                    defaults={
                        "status": Rider.Status.ONLINE,
                        "is_authorized": True,
                        "is_active": True,
                        "home_zone": node.zone,
                        "vehicle_type": bike,
                        "vehicle_model": "Honda CB 125",
                        "vehicle_plate_number": f"LG-{rider_index:04d}",
                        "onro_location_lat": node.latitude,
                        "onro_location_lng": node.longitude,
                        "current_latitude": node.latitude,
                        "current_longitude": node.longitude,
                        "city": "Lagos",
                    },
                )
                if not _:
                    # Was created by signal — update the important fields
                    rider.status = Rider.Status.ONLINE
                    rider.is_authorized = True
                    rider.is_active = True
                    rider.home_zone = node.zone
                    rider.vehicle_type = bike
                    rider.vehicle_model = "Honda CB 125"
                    rider.vehicle_plate_number = f"LG-{rider_index:04d}"
                    rider.onro_location_lat = node.latitude
                    rider.onro_location_lng = node.longitude
                    rider.current_latitude = node.latitude
                    rider.current_longitude = node.longitude
                    rider.city = "Lagos"
                    rider.save()

                self.stdout.write(
                    f"  Rider ✓ created: {contact_name} ({phone}) → {node.name}"
                )

