"""
Seed a realistic OCC dataset: 100 riders, 50 merchants, 2000+ orders across
20 zones, duty logs, snapshots, ratings, zone targets, captains, and leads.

Run:
  python manage.py seed_occ_full

Prerequisites:
  - seed_vehicles
  - seed_verticals_and_zones
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dispatcher.models import (
    DeliveryRating,
    Merchant,
    MerchantDailySnapshot,
    Rider,
    RiderDailySnapshot,
    RiderDutyLog,
    Vertical,
    VerticalLead,
    Zone,
    ZoneCaptain,
    ZoneTarget,
)
from orders.models import Delivery, Order, Vehicle

User = get_user_model()

HISTORY_DAYS = 30
NUM_RIDERS = 100
NUM_MERCHANTS = 50
ORDERS_PER_DAY_RANGE = (60, 120)  # platform-wide per day

LAGOS_AREAS = [
    ("Ikeja", "6.6059", "3.3491"),
    ("Lekki", "6.4531", "3.3958"),
    ("Surulere", "6.5061", "3.3665"),
    ("Yaba", "6.5062", "3.3782"),
    ("Gbagada", "6.5350", "3.3947"),
    ("Ajah", "6.4667", "3.5667"),
    ("Festac", "6.4664", "3.2835"),
    ("Ikorodu", "6.6000", "3.5000"),
    ("Oshodi", "6.5142", "3.3087"),
    ("Victoria Island", "6.4281", "3.4219"),
    ("Apapa", "6.4520", "3.3312"),
    ("Maryland", "6.5700", "3.3650"),
    ("Ogba", "6.6300", "3.3400"),
    ("Berger", "6.6470", "3.3742"),
    ("Agege", "6.6198", "3.3222"),
]

BUSINESS_NAMES = [
    "Tasty Bites", "Quick Eats Lagos", "Gadget Hub", "FreshMart",
    "Chops & Grills", "TechZone", "Island Pharmacy", "Mama's Kitchen",
    "AutoParts NG", "Fashion Forward", "BookWorld", "Clean Laundry Co",
    "GreenGrocer", "BabyStore NG", "PetCare Lagos", "FitFood Meals",
    "Office Supplies Pro", "HealthPlus", "CakesByNkem", "SmoothieBar",
    "NaijaSpares", "BeautyBox", "ElectroMart", "FoodBay",
    "SwiftPrint", "GlowSkin", "MeatShop NG", "DrinksDirect",
    "ToolBox Hardware", "LagosFlowers", "FurniturePlus", "JuicePress",
    "NaijaGifts", "PhoneHub", "FreshFish NG", "BakerStreet",
    "SportyNG", "LagosWines", "DairyFarm", "VeggieCrate",
    "SnackAttack", "SoupKitchen NG", "GadgetFix", "ShoeLocker",
    "PerfumeHouse", "LagosLinen", "CraftBeer NG", "SugarRush",
    "PastaPlace", "WrapKing",
]

RIDER_NAMES = [
    "Musa Ibrahim", "Chukwu Emeka", "Tunde Bakare", "Adamu Sule",
    "Femi Adesanya", "Yusuf Bello", "Kola Adeyemi", "Ife Okafor",
    "Hassan Abdullahi", "Segun Ojo", "Uche Nwankwo", "Gbenga Adu",
    "Ibrahim Musa", "Dayo Oluwole", "Chidi Obi", "Bayo Akindele",
    "Ahmed Lawal", "Tobi Fashola", "Kunle Peters", "Emeka Eze",
    "Victor Nnamdi", "Solomon Okeke", "James Okon", "Peter Udo",
    "Daniel Effiong", "Michael Bassey", "Samuel Ekpo", "Godwin Osagie",
    "Paul Igwe", "John Amadi", "Andrew Nwosu", "Stephen Chukwu",
    "David Eze", "Mark Obi", "Philip Okonkwo", "Thomas Agu",
    "Joseph Ajayi", "Francis Okoro", "Benjamin Uzor", "Charles Ike",
    "Abdulahi Garba", "Sani Danladi", "Kabiru Yusuf", "Abubakar Sadiq",
    "Muhammed Audu", "Idris Bala", "Aliyu Shehu", "Ismail Jibril",
    "Usman Abba", "Yakubu Musa", "Obinna Nze", "Chibueze Odo",
    "Ikechukwu Ani", "Nnamdi Uba", "Onyeka Diala", "Kenechukwu Ede",
    "Chinedu Agu", "Ugonna Okoye", "Ebuka Nnaji", "Somto Mbah",
    "Olumide Balogun", "Rotimi Coker", "Niyi Adeboye", "Wale Ogunyemi",
    "Dare Akinola", "Gbolahan Soyinka", "Folarin Bello", "Jide Sanwo",
    "Kayode Oladipo", "Ayo Makinde", "Tayo Adeleke", "Lekan Oseni",
    "Deji Ogunleye", "Bode Awolowo", "Akin Tijani", "Ladi Onabanjo",
    "Dele Momodu", "Lanre Falana", "Soji Abiodun", "Yinka Olatunde",
    "Remi Babalola", "Obi Cubana", "Nonso Dike", "Kene Mkparu",
    "Uzoma Okpara", "Afam Ohaeri", "Lotanna Igwe", "Jideofor Ezeilo",
    "Obiora Onyema", "Ifeanyichukwu Obi", "Uchenna Nwobi", "Azuka Obi",
    "Chukwuma Okeke", "Chinonso Eze", "Obioma Kalu", "Nkechi Okafor",
    "Amaka Nnadi", "Ngozi Okoli", "Chioma Udeh", "Ijeoma Nwachukwu",
]


class Command(BaseCommand):
    help = "Seed a full realistic OCC dataset for testing all endpoints."

    def handle(self, *args, **options):
        zones = list(Zone.objects.all())
        verticals = list(Vertical.objects.all())
        vehicles = list(Vehicle.objects.all())

        if not zones:
            self.stderr.write(self.style.ERROR("No zones. Run seed_verticals_and_zones first."))
            return
        if not vehicles:
            self.stderr.write(self.style.ERROR("No vehicles. Run seed_vehicles first."))
            return

        with transaction.atomic():
            merchants = self._create_merchants(zones)
            riders = self._create_riders(zones, vehicles)
            orders_created = self._create_orders(merchants, riders, vehicles, zones)
            self._create_zone_captains(zones)
            self._create_vertical_leads(verticals)
            self._create_zone_targets(zones)
            self._create_duty_logs(riders)
            self._create_rider_snapshots(riders)
            self._create_merchant_snapshots(merchants)
            self._create_delivery_ratings(riders)

        self.stdout.write(self.style.SUCCESS(
            f"Done: {len(riders)} riders, {len(merchants)} merchants, "
            f"{orders_created} orders, across {len(zones)} zones."
        ))

    # ------------------------------------------------------------------
    def _create_merchants(self, zones):
        self.stdout.write("Creating merchants...")
        merchants = list(Merchant.objects.select_related("user").all())
        existing = len(merchants)
        needed = max(0, NUM_MERCHANTS - existing)
        sources = ["experiential", "referral", "organic"]
        now = timezone.now()

        for i in range(needed):
            idx = existing + i
            phone = f"+23481{idx:08d}"
            name = BUSINESS_NAMES[idx % len(BUSINESS_NAMES)]
            if User.objects.filter(phone=phone).exists():
                continue

            user = User.objects.create_user(
                phone=phone,
                email=f"merchant{idx}@axpress.test",
                password="password123",
                business_name=name,
                contact_name=f"Owner of {name}",
                address=f"{random.randint(1, 200)} {random.choice(LAGOS_AREAS)[0]} Road, Lagos",
                usertype="Merchant",
            )
            merchant = Merchant.objects.get(user=user)
            merchant.zone = random.choice(zones)
            merchant.acquisition_source = random.choice(sources)
            roll = random.random()
            if roll < 0.65:
                merchant.activity_status = "active"
                merchant.last_order_date = now - timedelta(days=random.randint(0, 6))
            elif roll < 0.88:
                merchant.activity_status = "watch"
                merchant.last_order_date = now - timedelta(days=random.randint(8, 28))
            else:
                merchant.activity_status = "inactive"
                merchant.last_order_date = now - timedelta(days=random.randint(35, 90))
            merchant.save()
            merchants.append(merchant)

        # Update existing merchants that are missing zone assignments
        for m in merchants:
            if not m.zone:
                m.zone = random.choice(zones)
                m.acquisition_source = random.choice(sources)
                m.last_order_date = now - timedelta(days=random.randint(0, 30))
                m.save(update_fields=["zone", "acquisition_source", "last_order_date"])

        self.stdout.write(f"  {len(merchants)} merchants total ({needed} new).")
        return merchants

    # ------------------------------------------------------------------
    def _create_riders(self, zones, vehicles):
        self.stdout.write("Creating riders...")
        riders = list(Rider.objects.select_related("user").all())
        existing = len(riders)
        needed = max(0, NUM_RIDERS - existing)

        for i in range(needed):
            idx = existing + i
            phone = f"+23480{idx:08d}"
            name = RIDER_NAMES[idx % len(RIDER_NAMES)]
            if User.objects.filter(phone=phone).exists():
                continue

            user = User.objects.create_user(
                phone=phone,
                email=f"rider{idx}@axpress.test",
                password="password123",
                contact_name=name,
                usertype="Rider",
            )
            rider = Rider.objects.get(user=user)
            area = random.choice(LAGOS_AREAS)
            rider.home_zone = random.choice(zones)
            rider.vehicle_type = random.choice(vehicles)
            rider.status = random.choice(["online", "online", "online", "offline"])
            rider.is_authorized = True
            rider.current_latitude = Decimal(area[1]) + Decimal(str(random.uniform(-0.01, 0.01)))
            rider.current_longitude = Decimal(area[2]) + Decimal(str(random.uniform(-0.01, 0.01)))
            rider.current_speed = Decimal(str(random.choice([0, 0, 0, 5, 12, 25, 35])))
            rider.rating = Decimal(str(round(random.uniform(3.5, 5.0), 2)))
            rider.save()
            riders.append(rider)

        # Ensure existing riders have home zones
        for r in riders:
            if not r.home_zone:
                r.home_zone = random.choice(zones)
                r.is_authorized = True
                area = random.choice(LAGOS_AREAS)
                r.current_latitude = Decimal(area[1])
                r.current_longitude = Decimal(area[2])
                r.save(update_fields=[
                    "home_zone", "is_authorized",
                    "current_latitude", "current_longitude",
                ])

        self.stdout.write(f"  {len(riders)} riders total ({needed} new).")
        return riders

    # ------------------------------------------------------------------
    def _create_orders(self, merchants, riders, vehicles, zones):
        self.stdout.write("Creating orders...")
        now = timezone.now()
        statuses_weights = [
            ("Done", 55), ("Pending", 10), ("Assigned", 8),
            ("Started", 5), ("Pickup", 4), ("Fulfilling", 3),
            ("Arrived", 2), ("Failed", 6), ("CustomerCanceled", 4),
            ("RiderCanceled", 3),
        ]
        statuses = [s for s, _ in statuses_weights]
        weights = [w for _, w in statuses_weights]
        payment_methods = ["wallet", "wallet", "cash", "cash_on_pickup", "receiver_pays"]
        package_types = ["Box", "Envelope", "Fragile", "Food", "Document", "Other"]

        total_created = 0
        for days_ago in range(HISTORY_DAYS, -1, -1):
            day_base = now - timedelta(days=days_ago)
            num_orders = random.randint(*ORDERS_PER_DAY_RANGE)

            for _ in range(num_orders):
                merchant = random.choice(merchants)
                rider = random.choice(riders)
                vehicle = random.choice(vehicles)
                status_val = random.choices(statuses, weights=weights, k=1)[0]
                area_pickup = random.choice(LAGOS_AREAS)
                area_drop = random.choice(LAGOS_AREAS)
                dist = round(random.uniform(2.0, 25.0), 2)
                dur = int(dist * random.uniform(3.0, 6.0))
                amount = Decimal(str(round(random.uniform(1200, 8000), 2)))

                created_at = day_base.replace(
                    hour=random.randint(7, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                completed_at = None
                if status_val == "Done":
                    completed_at = created_at + timedelta(minutes=dur)

                order = Order(
                    user=merchant.user,
                    rider=rider if status_val not in ("Pending",) else None,
                    vehicle=vehicle,
                    mode="quick",
                    pickup_address=f"{random.randint(1, 300)} {area_pickup[0]} St, Lagos",
                    pickup_latitude=float(area_pickup[1]),
                    pickup_longitude=float(area_pickup[2]),
                    sender_name=merchant.user.contact_name or merchant.user.business_name,
                    sender_phone=merchant.user.phone,
                    payment_method=random.choice(payment_methods),
                    payment_status="Paid" if status_val == "Done" else "Pending",
                    total_amount=amount,
                    distance_km=Decimal(str(dist)),
                    duration_minutes=dur,
                    status=status_val,
                    created_at=created_at,
                    completed_at=completed_at,
                )
                order.save()

                # Create a delivery for each order
                Delivery.objects.create(
                    order=order,
                    dropoff_address=f"{random.randint(1, 300)} {area_drop[0]} Road, Lagos",
                    dropoff_latitude=float(area_drop[1]),
                    dropoff_longitude=float(area_drop[2]),
                    receiver_name=f"Customer {random.randint(1000, 9999)}",
                    receiver_phone=f"+23490{random.randint(10000000, 99999999)}",
                    package_type=random.choice(package_types),
                    status="Delivered" if status_val == "Done" else "Pending",
                    sequence=1,
                )
                total_created += 1

        self.stdout.write(f"  {total_created} orders created over {HISTORY_DAYS + 1} days.")
        return total_created

    # ------------------------------------------------------------------
    def _create_zone_captains(self, zones):
        count = 0
        for idx, zone in enumerate(zones):
            if hasattr(zone, "captain"):
                try:
                    zone.captain
                    continue
                except ZoneCaptain.DoesNotExist:
                    pass

            phone = f"+234900{idx:07d}"
            user, _ = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "email": f"captain.{zone.name.lower().replace(' ', '')}@axpress.test",
                    "contact_name": f"Captain {zone.name}",
                    "usertype": "ZoneCaptain",
                },
            )
            if not user.has_usable_password():
                user.set_password("password123")
                user.save(update_fields=["password"])
            ZoneCaptain.objects.get_or_create(user=user, defaults={"zone": zone})
            count += 1
        self.stdout.write(f"  {count} zone captains ensured.")

    # ------------------------------------------------------------------
    def _create_vertical_leads(self, verticals):
        count = 0
        for idx, vertical in enumerate(verticals):
            if hasattr(vertical, "lead"):
                try:
                    vertical.lead
                    continue
                except VerticalLead.DoesNotExist:
                    pass

            phone = f"+234800{idx:07d}"
            user, _ = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "email": f"lead.{vertical.code.lower()}@axpress.test",
                    "contact_name": vertical.lead_name,
                    "usertype": "VerticalLead",
                },
            )
            if not user.has_usable_password():
                user.set_password("password123")
                user.save(update_fields=["password"])
            VerticalLead.objects.get_or_create(user=user, defaults={"vertical": vertical})
            count += 1
        self.stdout.write(f"  {count} vertical leads ensured.")

    # ------------------------------------------------------------------
    def _create_zone_targets(self, zones):
        today = date.today()
        this_month = today.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        count = 0
        for zone in zones:
            for month in [last_month, this_month]:
                _, created = ZoneTarget.objects.get_or_create(
                    zone=zone,
                    month=month,
                    defaults={
                        "target_orders": random.randint(1500, 2500),
                        "target_revenue": Decimal(random.randint(400000, 800000)),
                    },
                )
                if created:
                    count += 1
        self.stdout.write(f"  {count} zone targets created.")

    # ------------------------------------------------------------------
    def _create_duty_logs(self, riders):
        if RiderDutyLog.objects.exists():
            self.stdout.write("  Duty logs already exist, skipping.")
            return

        self.stdout.write("Creating duty logs...")
        now = timezone.now()
        count = 0
        for rider in riders:
            for days_ago in range(HISTORY_DAYS, 0, -1):
                if random.random() > 0.82:
                    continue
                day_start = now - timedelta(days=days_ago)

                # Morning shift
                morning_on = day_start.replace(
                    hour=random.randint(6, 9), minute=random.randint(0, 59),
                    second=0, microsecond=0,
                )
                morning_off = morning_on + timedelta(
                    hours=random.randint(3, 6), minutes=random.randint(0, 59),
                )
                RiderDutyLog.objects.create(
                    rider=rider, went_online=morning_on, went_offline=morning_off,
                    duration_minutes=int((morning_off - morning_on).total_seconds() / 60),
                )
                count += 1

                if random.random() < 0.65:
                    aft_on = day_start.replace(
                        hour=random.randint(14, 17), minute=random.randint(0, 59),
                        second=0, microsecond=0,
                    )
                    aft_off = aft_on + timedelta(
                        hours=random.randint(2, 5), minutes=random.randint(0, 59),
                    )
                    RiderDutyLog.objects.create(
                        rider=rider, went_online=aft_on, went_offline=aft_off,
                        duration_minutes=int((aft_off - aft_on).total_seconds() / 60),
                    )
                    count += 1

        self.stdout.write(f"  {count} duty logs created.")

    # ------------------------------------------------------------------
    def _create_rider_snapshots(self, riders):
        if RiderDailySnapshot.objects.exists():
            self.stdout.write("  Rider snapshots exist, skipping.")
            return

        self.stdout.write("Creating rider snapshots...")
        today = date.today()
        count = 0
        for rider in riders:
            for days_ago in range(HISTORY_DAYS, 0, -1):
                snap_date = today - timedelta(days=days_ago)
                completed = random.randint(3, 20)
                RiderDailySnapshot.objects.create(
                    rider=rider, date=snap_date,
                    orders_completed=completed,
                    orders_rejected=random.randint(0, 3),
                    orders_failed=random.randint(0, 2),
                    revenue=Decimal(completed * random.randint(1500, 5000)),
                    distance_km=Decimal(str(round(completed * random.uniform(2.5, 7.0), 2))),
                    online_minutes=random.randint(200, 600),
                    peak_hour_minutes=random.randint(60, 300),
                    ghost_ride_minutes=random.choice([0, 0, 0, 0, 0, 15, 30]),
                )
                count += 1
        self.stdout.write(f"  {count} rider snapshots created.")

    # ------------------------------------------------------------------
    def _create_merchant_snapshots(self, merchants):
        if MerchantDailySnapshot.objects.exists():
            self.stdout.write("  Merchant snapshots exist, skipping.")
            return

        self.stdout.write("Creating merchant snapshots...")
        today = date.today()
        count = 0
        for merchant in merchants:
            for days_ago in range(HISTORY_DAYS, 0, -1):
                snap_date = today - timedelta(days=days_ago)
                placed = random.randint(1, 12)
                completed = max(0, placed - random.randint(0, 2))
                MerchantDailySnapshot.objects.create(
                    merchant=merchant.user, date=snap_date,
                    orders_placed=placed,
                    orders_completed=completed,
                    orders_failed=max(0, placed - completed - random.randint(0, 1)),
                    revenue=Decimal(completed * random.randint(1500, 5000)),
                )
                count += 1
        self.stdout.write(f"  {count} merchant snapshots created.")

    # ------------------------------------------------------------------
    def _create_delivery_ratings(self, riders):
        self.stdout.write("Creating delivery ratings...")
        done_orders = list(
            Order.objects.filter(status="Done", rider__isnull=False)
            .exclude(id__in=DeliveryRating.objects.values_list("order_id", flat=True))
            .select_related("rider")
            .order_by("?")[:500]
        )
        count = 0
        comments = [
            "", "Fast delivery!", "Great service", "Rider was polite",
            "Package arrived safely", "A bit late but okay", "Very professional",
            "Excellent!", "Good job", "Could be faster", "",
        ]
        for order in done_orders:
            DeliveryRating.objects.create(
                order=order, rider=order.rider,
                score=random.choices([1, 2, 3, 4, 5], weights=[2, 3, 10, 30, 55])[0],
                comment=random.choice(comments),
            )
            count += 1
        self.stdout.write(f"  {count} delivery ratings created.")
