"""
Seed all OCC-specific tables with realistic test data.

Prerequisites:
  - seed_vehicles (for Vehicle FK)
  - seed_verticals_and_zones (for Vertical / Zone rows)
  - populate_users (for base Merchant / Rider users)

Run:
  python manage.py seed_occ_test_data
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

User = get_user_model()

# How many days of historical snapshot / duty-log data to generate
HISTORY_DAYS = 30


class Command(BaseCommand):
    help = (
        "Seed OCC tables with test data: zone captains, vertical leads, "
        "duty logs, daily snapshots, delivery ratings, zone targets, and "
        "merchant field updates."
    )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self._assign_merchants_to_zones()
                self._create_zone_captains()
                self._create_vertical_leads()
                self._create_zone_targets()
                self._create_rider_duty_logs()
                self._create_rider_daily_snapshots()
                self._create_merchant_daily_snapshots()
                self._create_delivery_ratings()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Seeding failed: {e}"))
            raise

        self.stdout.write(self.style.SUCCESS("OCC test data seeded successfully."))

    # ------------------------------------------------------------------
    # 1. Assign existing Merchants to random Zones + set activity fields
    # ------------------------------------------------------------------
    def _assign_merchants_to_zones(self):
        zones = list(Zone.objects.all())
        if not zones:
            self.stdout.write(self.style.WARNING("No zones found — run seed_verticals_and_zones first."))
            return

        merchants = Merchant.objects.all()
        sources = ["experiential", "referral", "organic"]
        now = timezone.now()
        count = 0

        for merchant in merchants:
            merchant.zone = random.choice(zones)
            merchant.acquisition_source = random.choice(sources)
            # Randomly distribute activity: 60% active, 25% watch, 15% inactive
            roll = random.random()
            if roll < 0.60:
                merchant.activity_status = "active"
                merchant.last_order_date = now - timedelta(days=random.randint(0, 6))
            elif roll < 0.85:
                merchant.activity_status = "watch"
                merchant.last_order_date = now - timedelta(days=random.randint(8, 28))
            else:
                merchant.activity_status = "inactive"
                merchant.last_order_date = now - timedelta(days=random.randint(35, 90))
            merchant.save(
                update_fields=[
                    "zone",
                    "acquisition_source",
                    "activity_status",
                    "last_order_date",
                ]
            )
            count += 1

        self.stdout.write(f"  Assigned {count} merchants to zones.")

    # ------------------------------------------------------------------
    # 2. Create Zone Captains (one per zone, new User if needed)
    # ------------------------------------------------------------------
    def _create_zone_captains(self):
        zones = Zone.objects.all()
        count = 0

        for idx, zone in enumerate(zones):
            if hasattr(zone, "captain"):
                continue  # already has a captain

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

            ZoneCaptain.objects.get_or_create(
                user=user,
                defaults={"zone": zone},
            )
            count += 1

        self.stdout.write(f"  Created {count} zone captains.")

    # ------------------------------------------------------------------
    # 3. Create Vertical Leads (one per vertical, new User if needed)
    # ------------------------------------------------------------------
    def _create_vertical_leads(self):
        verticals = Vertical.objects.all()
        count = 0

        for idx, vertical in enumerate(verticals):
            if hasattr(vertical, "lead") and vertical.lead is not None:
                continue

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

            VerticalLead.objects.get_or_create(
                user=user,
                defaults={"vertical": vertical},
            )
            count += 1

        self.stdout.write(f"  Created {count} vertical leads.")

    # ------------------------------------------------------------------
    # 4. Create Zone Targets for current + previous month
    # ------------------------------------------------------------------
    def _create_zone_targets(self):
        zones = Zone.objects.all()
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

        self.stdout.write(f"  Created {count} zone targets.")

    # ------------------------------------------------------------------
    # 5. Create Rider Duty Logs (past N days)
    # ------------------------------------------------------------------
    def _create_rider_duty_logs(self):
        riders = list(Rider.objects.all())
        if not riders:
            self.stdout.write(self.style.WARNING("No riders found — run populate_users first."))
            return

        now = timezone.now()
        count = 0

        for rider in riders:
            # Skip if rider already has duty logs
            if RiderDutyLog.objects.filter(rider=rider).exists():
                continue

            for days_ago in range(HISTORY_DAYS, 0, -1):
                # ~80% chance the rider worked on any given day
                if random.random() > 0.80:
                    continue

                day_start = now - timedelta(days=days_ago)

                # Morning shift
                morning_on = day_start.replace(
                    hour=random.randint(7, 9),
                    minute=random.randint(0, 59),
                    second=0,
                    microsecond=0,
                )
                morning_off = morning_on + timedelta(
                    hours=random.randint(3, 5),
                    minutes=random.randint(0, 59),
                )
                dur_m = int((morning_off - morning_on).total_seconds() / 60)
                RiderDutyLog.objects.create(
                    rider=rider,
                    went_online=morning_on,
                    went_offline=morning_off,
                    duration_minutes=dur_m,
                )
                count += 1

                # ~60% chance of an afternoon/evening shift
                if random.random() < 0.60:
                    afternoon_on = day_start.replace(
                        hour=random.randint(14, 17),
                        minute=random.randint(0, 59),
                        second=0,
                        microsecond=0,
                    )
                    afternoon_off = afternoon_on + timedelta(
                        hours=random.randint(2, 5),
                        minutes=random.randint(0, 59),
                    )
                    dur_a = int(
                        (afternoon_off - afternoon_on).total_seconds() / 60
                    )
                    RiderDutyLog.objects.create(
                        rider=rider,
                        went_online=afternoon_on,
                        went_offline=afternoon_off,
                        duration_minutes=dur_a,
                    )
                    count += 1

        self.stdout.write(f"  Created {count} rider duty logs.")

    # ------------------------------------------------------------------
    # 6. Create Rider Daily Snapshots (past N days)
    # ------------------------------------------------------------------
    def _create_rider_daily_snapshots(self):
        riders = list(Rider.objects.all())
        if not riders:
            return

        today = date.today()
        count = 0

        for rider in riders:
            if RiderDailySnapshot.objects.filter(rider=rider).exists():
                continue

            for days_ago in range(HISTORY_DAYS, 0, -1):
                snap_date = today - timedelta(days=days_ago)
                completed = random.randint(5, 25)
                rejected = random.randint(0, 3)
                failed = random.randint(0, 2)
                revenue = Decimal(completed * random.randint(1200, 4500))
                distance = Decimal(str(round(completed * random.uniform(2.0, 8.0), 2)))
                online_mins = random.randint(180, 600)
                peak_mins = random.randint(60, min(online_mins, 360))
                ghost_mins = random.choice([0, 0, 0, 0, 15, 30])  # mostly 0

                RiderDailySnapshot.objects.create(
                    rider=rider,
                    date=snap_date,
                    orders_completed=completed,
                    orders_rejected=rejected,
                    orders_failed=failed,
                    revenue=revenue,
                    distance_km=distance,
                    online_minutes=online_mins,
                    peak_hour_minutes=peak_mins,
                    ghost_ride_minutes=ghost_mins,
                )
                count += 1

        self.stdout.write(f"  Created {count} rider daily snapshots.")

    # ------------------------------------------------------------------
    # 7. Create Merchant Daily Snapshots (past N days)
    # ------------------------------------------------------------------
    def _create_merchant_daily_snapshots(self):
        merchants = list(Merchant.objects.select_related("user").all())
        if not merchants:
            return

        today = date.today()
        count = 0

        for merchant in merchants:
            if MerchantDailySnapshot.objects.filter(merchant=merchant.user).exists():
                continue

            for days_ago in range(HISTORY_DAYS, 0, -1):
                snap_date = today - timedelta(days=days_ago)
                placed = random.randint(1, 15)
                completed = max(0, placed - random.randint(0, 3))
                failed = max(0, placed - completed - random.randint(0, 1))
                revenue = Decimal(completed * random.randint(1500, 5000))

                MerchantDailySnapshot.objects.create(
                    merchant=merchant.user,
                    date=snap_date,
                    orders_placed=placed,
                    orders_completed=completed,
                    orders_failed=failed,
                    revenue=revenue,
                )
                count += 1

        self.stdout.write(f"  Created {count} merchant daily snapshots.")

    # ------------------------------------------------------------------
    # 8. Create Delivery Ratings for completed orders
    # ------------------------------------------------------------------
    def _create_delivery_ratings(self):
        from orders.models import Order

        completed_orders = (
            Order.objects.filter(status="Done", rider__isnull=False)
            .exclude(rating__isnull=False)
            .select_related("rider")[:100]
        )
        count = 0

        for order in completed_orders:
            if DeliveryRating.objects.filter(order=order).exists():
                continue

            DeliveryRating.objects.create(
                order=order,
                rider=order.rider,
                score=random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[2, 3, 10, 30, 55],  # skewed positive
                )[0],
                comment=random.choice([
                    "",
                    "Fast delivery!",
                    "Great service",
                    "Rider was polite",
                    "Package arrived safely",
                    "A bit late but okay",
                    "Took too long",
                    "",
                ]),
            )
            count += 1

        self.stdout.write(f"  Created {count} delivery ratings.")
