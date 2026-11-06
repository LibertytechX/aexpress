"""
Seed realistic test data for exercising the Operations Dashboard endpoints.

Creates (defaults): 10 merchants, 25 riders (each with a GPS location + a
VehicleAsset), and 90 orders spread across all merchants and assigned round-robin
to all riders. Orders are marked with real project statuses (Done / enroute /
Pending / cancelled), 20 are COD, every order gets a payment method+status, and
delivered orders get a RiderEarning (commission). Vehicles carry telemetry so the
tracking dashboard has live/offline/moving data.

After seeding it runs the alert engine over the new data, so the alert endpoints
have real alerts to show (incomplete/stuck/delayed orders, GPS offline, speeding,
ghost-ride, COD retention, insurance/registration expiring, …). A few rider
anomalies are seeded deliberately so those rules fire regardless of time of day.

Idempotent: re-running clears the prior seed (tagged by phone/plate prefix) and
ALL alerts first.

Usage:
    python manage.py seed_ops_test_data
    python manage.py seed_ops_test_data --merchants 10 --riders 25 --orders 90 --cod 20
    python manage.py seed_ops_test_data --append      # keep existing seed data
    python manage.py seed_ops_test_data --no-alerts    # skip alert generation
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

MERCHANT_PREFIX = "234815"   # merchant user phones
RIDER_PREFIX = "234816"      # rider user phones
PLATE_PREFIX = "SEED-"       # vehicle asset plates

ENROUTE_STATUSES = ["Started", "Pickup", "Fulfilling", "Arrived"]
CANCELLED_STATUSES = ["CustomerCanceled", "RiderCanceled"]
PAYMENT_METHODS = [
    "wallet", "cash", "cash_on_pickup", "receiver_pays", "postpaid", "subscription"
]
LAGOS_LAT, LAGOS_LNG = 6.4550, 3.3940


class Command(BaseCommand):
    help = "Seed merchants, riders, vehicles and orders for ops-dashboard testing."

    def add_arguments(self, parser):
        parser.add_argument("--merchants", type=int, default=10)
        parser.add_argument("--riders", type=int, default=25)
        parser.add_argument("--orders", type=int, default=90)
        parser.add_argument("--cod", type=int, default=20)
        parser.add_argument(
            "--append", action="store_true", help="Keep existing seed data."
        )
        parser.add_argument(
            "--no-alerts", action="store_true",
            help="Skip running the alert engine after seeding.",
        )

    def handle(self, *args, **opts):
        from authentication.models import User
        from dispatcher.models import Rider, VehicleAsset
        from orders.models import Order, Vehicle
        from riders.models import RiderCodRecord, RiderEarning

        random.seed(42)
        now = timezone.now()
        today = timezone.localdate()

        with transaction.atomic():
            if not opts["append"]:
                self._clear(User, VehicleAsset)

            # ── Vehicle (fare) types ────────────────────────────────
            vtypes = {}
            for name, mw, bf, vtype in [
                ("Bike", 20, 500, "bike"),
                ("Car", 200, 1000, "car"),
                ("Van", 800, 1500, "van"),
            ]:
                v, _ = Vehicle.objects.get_or_create(
                    name=name,
                    defaults={"max_weight_kg": mw, "base_price": bf,
                              "base_fare": bf, "rate_per_km": 100},
                )
                vtypes[vtype] = v

            # ── Merchants ───────────────────────────────────────────
            merchants = []
            for i in range(opts["merchants"]):
                u = User.objects.create(
                    phone=f"{MERCHANT_PREFIX}{i:06d}",
                    email=f"seed.merchant{i}@axpress.test",
                    business_name=f"Seed Merchant {i+1}",
                    contact_name=f"Merchant Contact {i+1}",
                    usertype="Merchant",
                    registration_source="experiential",
                )
                # dispatcher.Merchant is auto-created by a post_save signal.
                merchants.append(u)

            # ── Riders (+ vehicle asset + GPS location) ─────────────
            riders = []
            rider_statuses = ["online", "on_delivery", "offline"]
            for i in range(opts["riders"]):
                vtype = random.choices(
                    ["bike", "car", "van"], weights=[7, 2, 1]
                )[0]

                # Deliberate anomalies so alert rules fire regardless of time:
                #   i 0..2 → speeding (vehicle ≥ 85 km/h, fresh telemetry)
                #   i 3..4 → ghost ride (rider offline but vehicle moving)
                if i < 3:
                    rstatus, rider_moving = "on_delivery", True
                    veh_speed = Decimal(str(random.randint(85, 130)))
                    rider_speed, ping_age = veh_speed, random.randint(1, 8)
                elif i < 5:
                    rstatus, rider_moving = "offline", False
                    veh_speed = Decimal(str(random.randint(10, 40)))
                    rider_speed, ping_age = Decimal("0"), random.randint(1, 8)
                else:
                    rstatus = random.choice(rider_statuses)
                    rider_moving = (
                        rstatus == "on_delivery" and random.random() < 0.7
                    )
                    veh_speed = (
                        Decimal(str(random.randint(8, 55))) if rider_moving
                        else Decimal("0")
                    )
                    rider_speed = veh_speed
                    ping_age = random.randint(1, 20) if rstatus != "offline" \
                        else random.randint(5, 600)

                lat = round(LAGOS_LAT + random.uniform(-0.15, 0.15), 6)
                lng = round(LAGOS_LNG + random.uniform(-0.15, 0.15), 6)

                asset = VehicleAsset.objects.create(
                    plate_number=f"{PLATE_PREFIX}{i:03d}",
                    vehicle_type=vtype,
                    make="QLINK", model="champion",
                    engine_status=(
                        "on" if veh_speed > 0 else random.choice(["off", "idle"])
                    ),
                    speed=veh_speed,
                    latitude=Decimal(str(lat)), longitude=Decimal(str(lng)),
                    last_telemetry_at=now - timedelta(minutes=ping_age),
                    insurance_expiry=today + timedelta(days=random.randint(-5, 150)),
                    registration_expiry=today + timedelta(days=random.randint(20, 300)),
                    is_active=True,
                )
                u = User.objects.create(
                    phone=f"{RIDER_PREFIX}{i:06d}",
                    email=f"seed.rider{i}@axpress.test",
                    business_name="",
                    contact_name=f"Seed Rider {i+1}",
                    usertype="Rider",
                )
                # Rider profile is auto-created by a post_save signal; enrich it.
                r = Rider.objects.get(user=u)
                r.vehicle_type = vtypes[vtype]
                r.vehicle_asset = asset
                r.status = rstatus
                r.is_authorized = True
                r.is_moving = rider_moving
                r.current_latitude = Decimal(str(lat))
                r.current_longitude = Decimal(str(lng))
                r.current_speed = rider_speed
                r.last_location_update = now - timedelta(minutes=ping_age)
                r.save()
                riders.append(r)

            # ── Orders ──────────────────────────────────────────────
            n = opts["orders"]
            done_n, enroute_n, pending_n = 50, 20, 10
            if n != 90:  # scale buckets proportionally
                done_n = int(n * 0.56); enroute_n = int(n * 0.22)
                pending_n = int(n * 0.11)
            cod_indices = set(random.sample(range(n), min(opts["cod"], n)))

            created = {"Done": 0, "enroute": 0, "Pending": 0, "cancelled": 0,
                       "cod": 0, "earnings": 0, "cod_records": 0}

            for i in range(n):
                merchant = merchants[i % len(merchants)]
                rider = riders[i % len(riders)]
                vehicle = rider.vehicle_type or vtypes["bike"]

                if i < done_n:
                    status = "Done"
                elif i < done_n + enroute_n:
                    status = random.choice(ENROUTE_STATUSES)
                elif i < done_n + enroute_n + pending_n:
                    status = "Pending"
                else:
                    status = random.choice(CANCELLED_STATUSES)

                created_at = now - timedelta(
                    days=random.randint(0, 20), hours=random.randint(0, 23)
                )
                total = Decimal(str(random.randint(800, 6000)))
                is_cod = i in cod_indices
                cod_amount = (
                    Decimal(str(random.randint(1500, 20000))) if is_cod else Decimal("0")
                )

                # payment
                if is_cod:
                    method = random.choice(["cash", "receiver_pays", "cash_on_pickup"])
                else:
                    method = random.choice(PAYMENT_METHODS)
                if status == "Done":
                    pay_status = "Postpaid" if method == "postpaid" else "Paid"
                elif status in CANCELLED_STATUSES:
                    pay_status = "Cancelled"
                else:
                    pay_status = "Pending"

                # timestamps
                assigned_at = picked_up_at = arrived_at = None
                completed_at = canceled_at = None
                if status not in ("Pending",):
                    assigned_at = created_at + timedelta(minutes=5)
                if status in ENROUTE_STATUSES or status == "Done":
                    picked_up_at = assigned_at + timedelta(minutes=15)
                if status in ("Arrived", "Done"):
                    arrived_at = picked_up_at + timedelta(minutes=20)
                if status == "Done":
                    completed_at = picked_up_at + timedelta(minutes=30)
                if status in CANCELLED_STATUSES:
                    canceled_at = created_at + timedelta(minutes=20)

                order = Order.objects.create(
                    user=merchant, vehicle=vehicle, rider=rider,
                    pickup_address="12 Marina Rd, Lagos Island",
                    sender_name=merchant.business_name, sender_phone=merchant.phone,
                    total_amount=total, payment_method=method,
                    payment_status=pay_status, status=status,
                    collect_on_delivery=is_cod, cod_amount=cod_amount,
                    distance_km=Decimal(str(random.randint(1, 25))),
                    duration_minutes=random.randint(10, 90),
                    created_at=created_at, assigned_at=assigned_at,
                    picked_up_at=picked_up_at, arrived_at=arrived_at,
                    completed_at=completed_at, canceled_at=canceled_at,
                )

                if status == "Done":
                    created["Done"] += 1
                elif status in ENROUTE_STATUSES:
                    created["enroute"] += 1
                elif status == "Pending":
                    created["Pending"] += 1
                else:
                    created["cancelled"] += 1

                # rider commission (delivered orders)
                if status == "Done":
                    RiderEarning.objects.create(
                        rider=rider, order=order,
                        base_fare=(total * Decimal("0.5")).quantize(Decimal("0.01")),
                        distance_fare=(total * Decimal("0.3")).quantize(Decimal("0.01")),
                        commission_pct=Decimal("20.00"),
                        commission_amount=(total * Decimal("0.2")).quantize(Decimal("0.01")),
                        net_earning=(total * Decimal("0.8")).quantize(Decimal("0.01")),
                        cod_amount=cod_amount,
                    )
                    created["earnings"] += 1

                # COD record (reconciliation)
                if is_cod:
                    created["cod"] += 1
                    if status == "Done":
                        rec_status = random.choices(
                            ["remitted", "verified", "pending"], weights=[4, 3, 3]
                        )[0]
                    else:
                        rec_status = "pending"
                    rec = RiderCodRecord.objects.create(
                        rider=rider, order=order, amount=cod_amount,
                        status=rec_status,
                        remitted_at=(now if rec_status != "pending" else None),
                    )
                    # backdate so COD ageing buckets populate
                    RiderCodRecord.objects.filter(pk=rec.pk).update(
                        created_at=(completed_at or created_at)
                    )
                    created["cod_records"] += 1

        # ── Generate alerts from the seeded data (real engine run) ──
        alerts = None
        if not opts["no_alerts"]:
            from io import StringIO

            from django.core.management import call_command

            from oprtn_dashboard.alerts.engine import run_all_rules

            call_command("seed_alert_rules", stdout=StringIO())  # ensure rules
            alerts = run_all_rules()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {len(merchants)} merchants, {len(riders)} riders, "
            f"{n} orders "
            f"(Done={created['Done']}, enroute={created['enroute']}, "
            f"Pending={created['Pending']}, cancelled={created['cancelled']}), "
            f"COD={created['cod']}, earnings={created['earnings']}, "
            f"cod_records={created['cod_records']}."
        ))
        if alerts:
            self.stdout.write(self.style.SUCCESS(
                f"Alerts: created={alerts['created']}, "
                f"updated={alerts['updated']}, resolved={alerts['resolved']} "
                f"(evaluators run={alerts['evaluated']})."
            ))
        self.stdout.write(
            "Test the endpoints, e.g.:\n"
            "  GET /api/ops/order-dashboard/?filter=this_month\n"
            "  GET /api/ops/tracking-dashboard/\n"
            "  GET /api/ops/payments/?filter=this_month\n"
            "  GET /api/ops/cod-dashboard/?filter=this_month"
        )

    def _clear(self, User, VehicleAsset):
        """Remove previously-seeded data (by phone/plate prefix) and all alerts."""
        from oprtn_dashboard.models import Alert

        User.objects.filter(phone__startswith=MERCHANT_PREFIX).delete()
        User.objects.filter(phone__startswith=RIDER_PREFIX).delete()
        VehicleAsset.objects.filter(plate_number__startswith=PLATE_PREFIX).delete()
        Alert.objects.all().delete()
