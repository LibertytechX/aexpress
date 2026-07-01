"""
Tests for the Operations Dashboard app — covers Phases 1–5.

Run:  python manage.py test oprtn_dashboard
"""

import hashlib
import secrets
from datetime import datetime, time, timedelta
from decimal import Decimal
from io import BytesIO, StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import Rider, ServiceAPIKey, VehicleAsset
from orders.models import Order, Vehicle
from riders.models import RiderCodRecord

from .alerts.engine import run_all_rules
from .filters import parse_filter
from .metrics import cod_metrics, payment_metrics
from .models import Alert, AlertRule, AlertStatus, AlertType, FuelBill


FUEL_HEADER = [
    "Invoice number", "Branch", "Vehicle", "Vehicle brand", "Vehicle model ",
    "Internal number", "Trip number ", "Type of fuel", "Fuel price", "Cost",
    "Worker tip", "Km/L", "L/100 Km", "Number of liters", "Odometer",
    "Payment method", "delegate", "The station", "Station branch",
    "Governorate - City - District", "Station location", "Date",
]


def make_fuel_xlsx(rows):
    """Build an in-memory .xlsx matching the fuel bills format."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(FUEL_HEADER)
    for r in rows:
        ws.append(r)
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    bio.name = "bills.xlsx"
    return bio


def fuel_row(invoice, plate, cost, liters, when, fuel_price=1200, kmpl=200):
    return [
        invoice, "HQ", plate, "QLINK", "champ", plate, "-", "Petrol",
        fuel_price, cost, 40, kmpl, 0.5, liters, 52000, "From the balance",
        plate, "Station A", "SA Branch", "Lagos - Eti-Osa - VI",
        "6.4,3.4", when,
    ]


# ---------------------------------------------------------------------------
# Shared base: seeded rules, factories, and an authed API client.
# ---------------------------------------------------------------------------


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ops-test",
        }
    }
)
class OpsTestBase(TestCase):
    def setUp(self):
        cache.clear()
        call_command("seed_alert_rules", stdout=StringIO())
        self.raw_key = "sk_" + secrets.token_hex(24)
        ServiceAPIKey.objects.create(
            name="test-key",
            prefix=self.raw_key[:11],
            key_hash=hashlib.sha256(self.raw_key.encode()).hexdigest(),
            scopes=["occ:read", "occ:write"],
            is_active=True,
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.raw_key)

    # ── factories ───────────────────────────────────────────────────
    _phone_seq = 0

    def make_user(self, contact="Tess", business="TestMart"):
        OpsTestBase._phone_seq += 1
        phone = f"234810000{OpsTestBase._phone_seq:04d}"
        return User.objects.create(
            phone=phone,
            email=f"{phone}@t.com",
            business_name=business,
            contact_name=contact,
        )

    def make_vehicle(self, name="TBike"):
        return Vehicle.objects.create(
            name=name, max_weight_kg=20, base_price=0
        )

    def make_rider(self):
        return Rider.objects.create(user=self.make_user(contact="Ryder"))

    def make_order(self, merchant, vehicle, amount=1000, method="wallet",
                   status="Done", cod=False, cod_amt=0, rider=None):
        return Order.objects.create(
            user=merchant, vehicle=vehicle, rider=rider, pickup_address="addr",
            sender_name="s", sender_phone="p", total_amount=Decimal(str(amount)),
            payment_method=method, status=status,
            collect_on_delivery=cod, cod_amount=Decimal(str(cod_amt)),
        )

    def make_asset(self, plate, **kw):
        return VehicleAsset.objects.create(plate_number=plate, **kw)


# ---------------------------------------------------------------------------
# Phase 1 — scaffold, wiring, auth, health
# ---------------------------------------------------------------------------


class Phase1HealthTests(OpsTestBase):
    # Auth disabled on oprtn_dashboard views — anonymous access now allowed.
    # def test_health_requires_auth(self):
    #     anon = APIClient()
    #     self.assertIn(anon.get("/api/ops/health/").status_code, (401, 403))

    def test_health_ok_with_key(self):
        r = self.client.get("/api/ops/health/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["app"], "oprtn_dashboard")
        self.assertIn("date_range", body)


# ---------------------------------------------------------------------------
# Phase 3 — models, seed, constraint
# ---------------------------------------------------------------------------


class Phase3ModelTests(OpsTestBase):
    def test_seed_creates_all_rules_idempotent(self):
        self.assertEqual(AlertRule.objects.count(), len(AlertType.choices))
        call_command("seed_alert_rules", stdout=StringIO())  # again
        self.assertEqual(AlertRule.objects.count(), len(AlertType.choices))

    def test_open_alert_unique_constraint(self):
        Alert.objects.create(
            alert_type=AlertType.GHOST_RIDE, entity_type="rider",
            title="a", dedupe_key="K1",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Alert.objects.create(
                    alert_type=AlertType.GHOST_RIDE, entity_type="rider",
                    title="b", dedupe_key="K1",
                )

    def test_resolve_allows_new_open_with_same_key(self):
        a = Alert.objects.create(
            alert_type=AlertType.GHOST_RIDE, entity_type="rider",
            title="a", dedupe_key="K2",
        )
        a.resolve(note="done")
        self.assertEqual(a.status, AlertStatus.RESOLVED)
        self.assertIsNotNone(a.resolved_at)
        # a new open alert with the same key is now allowed
        b = Alert.objects.create(
            alert_type=AlertType.GHOST_RIDE, entity_type="rider",
            title="b", dedupe_key="K2",
        )
        self.assertEqual(b.status, AlertStatus.NEW)


# ---------------------------------------------------------------------------
# Phase 4 — engine + evaluators
# ---------------------------------------------------------------------------


class Phase4EngineTests(OpsTestBase):
    def test_bike_after_hours_fires_and_autoresolves(self):
        rule = AlertRule.objects.get(alert_type=AlertType.BIKE_AFTER_HOURS)
        rule.params = {**rule.params, "curfew_start_hour": 0, "curfew_end_hour": 24}
        rule.save()
        va = self.make_asset(
            "BAH1", vehicle_type="bike", speed=30,
            last_telemetry_at=timezone.now(),
        )
        run_all_rules(only_types=[AlertType.BIKE_AFTER_HOURS])
        self.assertEqual(
            Alert.objects.filter(
                alert_type=AlertType.BIKE_AFTER_HOURS, status="new"
            ).count(),
            1,
        )
        # bike stops -> auto-resolve
        va.speed = 0
        va.save()
        run_all_rules(only_types=[AlertType.BIKE_AFTER_HOURS])
        self.assertEqual(
            Alert.objects.get(alert_type=AlertType.BIKE_AFTER_HOURS).status,
            AlertStatus.RESOLVED,
        )

    def test_engine_dedupes_not_duplicates(self):
        rule = AlertRule.objects.get(alert_type=AlertType.BIKE_AFTER_HOURS)
        rule.params = {**rule.params, "curfew_start_hour": 0, "curfew_end_hour": 24}
        rule.save()
        self.make_asset(
            "BAH2", vehicle_type="bike", speed=30,
            last_telemetry_at=timezone.now(),
        )
        s1 = run_all_rules(only_types=[AlertType.BIKE_AFTER_HOURS])
        s2 = run_all_rules(only_types=[AlertType.BIKE_AFTER_HOURS])
        self.assertEqual(s1["created"], 1)
        self.assertEqual(s2["created"], 0)
        self.assertEqual(s2["updated"], 1)
        self.assertEqual(Alert.objects.filter(status="new").count(), 1)

    def test_speed_violation_severity_tiering(self):
        self.make_asset(
            "SPD1", vehicle_type="bike", speed=130,
            last_telemetry_at=timezone.now(),
        )
        run_all_rules(only_types=[AlertType.SPEED_VIOLATION])
        a = Alert.objects.get(alert_type=AlertType.SPEED_VIOLATION)
        self.assertEqual(a.severity, "critical")
        self.assertEqual(a.value, Decimal("130.00"))

    def test_gps_offline_fires(self):
        self.make_asset(
            "GPS1", vehicle_type="bike", speed=0, is_active=True,
            last_telemetry_at=timezone.now() - timedelta(hours=3),
        )
        run_all_rules(only_types=[AlertType.GPS_OFFLINE])
        self.assertTrue(
            Alert.objects.filter(alert_type=AlertType.GPS_OFFLINE).exists()
        )

    def test_insurance_expiring_critical(self):
        self.make_asset(
            "INS1", vehicle_type="bike",
            insurance_expiry=timezone.localdate() + timedelta(days=10),
        )
        run_all_rules(only_types=[AlertType.INSURANCE_EXPIRING])
        a = Alert.objects.get(alert_type=AlertType.INSURANCE_EXPIRING)
        self.assertEqual(a.severity, "critical")  # 10d <= 30d critical

    def test_incomplete_order_fires(self):
        m, v = self.make_user(), self.make_vehicle()
        order = self.make_order(m, v, status="Started")
        Order.objects.filter(pk=order.pk).update(
            assigned_at=timezone.now() - timedelta(hours=7)
        )
        run_all_rules(only_types=[AlertType.INCOMPLETE_ORDER])
        a = Alert.objects.get(alert_type=AlertType.INCOMPLETE_ORDER)
        self.assertEqual(a.order_id, order.id)

    def test_cod_retention_fires(self):
        m, v, rider = self.make_user(), self.make_vehicle(), self.make_rider()
        order = self.make_order(m, v, status="Done", cod=True, cod_amt=2000)
        rec = RiderCodRecord.objects.create(
            rider=rider, order=order, amount=Decimal("2000"), status="pending"
        )
        RiderCodRecord.objects.filter(pk=rec.pk).update(
            created_at=timezone.now() - timedelta(hours=30)
        )
        run_all_rules(only_types=[AlertType.COD_RETENTION])
        self.assertTrue(
            Alert.objects.filter(alert_type=AlertType.COD_RETENTION).exists()
        )


# ---------------------------------------------------------------------------
# Phase 4/5 — alert endpoints
# ---------------------------------------------------------------------------


class AlertEndpointTests(OpsTestBase):
    def _make_alert(self, **kw):
        defaults = dict(
            alert_type=AlertType.GHOST_RIDE, entity_type="rider",
            severity="high", title="t", dedupe_key=secrets.token_hex(6),
        )
        defaults.update(kw)
        return Alert.objects.create(**defaults)

    def test_list_defaults_to_active(self):
        self._make_alert()  # new
        resolved = self._make_alert()
        resolved.resolve()
        data = self.client.get("/api/ops/alerts/").json()["data"]
        self.assertEqual(data["count"], 1)  # only the open one

    def test_resolve_endpoint(self):
        a = self._make_alert()
        r = self.client.post(
            f"/api/ops/alerts/{a.id}/resolve/",
            {"status": "resolved", "resolution_note": "fixed"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.status, AlertStatus.RESOLVED)

    def test_generate_endpoint(self):
        r = self.client.post("/api/ops/alerts/generate/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("evaluated", r.json()["data"])

    def test_alert_dashboard(self):
        self._make_alert(severity="critical")
        data = self.client.get(
            "/api/ops/alert-dashboard/?period=this_month"
        ).json()["data"]
        self.assertEqual(data["active"]["total"], 1)
        self.assertEqual(data["active"]["by_severity"]["critical"], 1)
        self.assertEqual(data["period_summary"]["total"], 1)

    def test_alert_rules_list_and_patch(self):
        listing = self.client.get("/api/ops/alert-rules/").json()["data"]
        self.assertEqual(len(listing), len(AlertType.choices))
        rid = listing[0]["id"]
        r = self.client.patch(
            f"/api/ops/alert-rules/{rid}/", {"is_enabled": False}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["is_enabled"])

    # Auth disabled on oprtn_dashboard views — scope no longer enforced.
    # def test_write_endpoint_rejects_readonly_key(self):
    #     raw = "sk_" + secrets.token_hex(24)
    #     ServiceAPIKey.objects.create(
    #         name="ro", prefix=raw[:11],
    #         key_hash=hashlib.sha256(raw.encode()).hexdigest(),
    #         scopes=["occ:read"], is_active=True,
    #     )
    #     ro = APIClient()
    #     ro.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
    #     r = ro.post("/api/ops/alerts/generate/", {}, format="json")
    #     self.assertEqual(r.status_code, 403)


# ---------------------------------------------------------------------------
# Phase 2 / 5 — payment + COD metrics & endpoints
# ---------------------------------------------------------------------------


class PaymentCodTests(OpsTestBase):
    def setUp(self):
        super().setUp()
        self.m = self.make_user()
        self.v = self.make_vehicle()
        # 1000 wallet Done | 500 cash Done COD2000 | 800 postpaid Pending
        self.make_order(self.m, self.v, 1000, "wallet", "Done")
        self.o_cod = self.make_order(
            self.m, self.v, 500, "cash", "Done", cod=True, cod_amt=2000
        )
        self.make_order(self.m, self.v, 800, "postpaid", "Pending")

    def test_payment_breakdown(self):
        qs = Order.objects.all()
        d = payment_metrics.payment_breakdown(qs)
        self.assertEqual(d["total_amount"], "2300.00")
        self.assertEqual(d["recognized_revenue"], "1500.00")
        timing = d["by_collection_timing"]
        self.assertEqual(timing["prepaid"]["amount"], "1000.00")
        self.assertEqual(timing["rider_collected"]["amount"], "500.00")
        self.assertEqual(timing["deferred"]["amount"], "800.00")

    def test_cod_fee_and_reconciliation(self):
        d = cod_metrics.cod_dashboard(Order.objects.all())
        cards = d["cards"]
        self.assertEqual(cards["total_orders"], 1)
        self.assertEqual(cards["delivered"], 1)
        self.assertEqual(cards["cod_expected"], "2000.00")
        # fee = flat 500 + 1.5% * 2000 = 530
        self.assertEqual(cards["cod_fees_earned"], "530.00")
        self.assertEqual(cards["cod_outstanding"], "2000.00")
        self.assertEqual(cards["delivery_rate"], 100.0)

    def test_cod_ageing_and_collected(self):
        rider = self.make_rider()
        rec = RiderCodRecord.objects.create(
            rider=rider, order=self.o_cod, amount=Decimal("2000"),
            status="pending",
        )
        RiderCodRecord.objects.filter(pk=rec.pk).update(
            created_at=timezone.now() - timedelta(hours=60)
        )
        d = cod_metrics.cod_dashboard(Order.objects.all())
        self.assertEqual(d["ageing"]["48h_plus"]["count"], 1)
        rec.status = "remitted"
        rec.save()
        d2 = cod_metrics.cod_dashboard(Order.objects.all())
        self.assertEqual(d2["cards"]["cod_collected"], "2000.00")
        self.assertEqual(d2["cards"]["cod_outstanding"], "0.00")

    def test_payments_endpoint(self):
        r = self.client.get("/api/ops/payments/?period=this_month")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["total_amount"], "2300.00")

    def test_cod_endpoint(self):
        r = self.client.get("/api/ops/cod-dashboard/?period=this_month")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["cards"]["cod_fees_earned"], "530.00")

    def test_payment_orders_drilldown(self):
        # setUp made: 1000 wallet Done, 500 cash Done (COD), 800 postpaid Pending
        base = "/api/ops/payments/orders/?period=this_month"
        all_orders = self.client.get(base).json()["data"]
        self.assertEqual(all_orders["count"], 3)
        self.assertIn("order_number", all_orders["results"][0])
        self.assertIn("merchant", all_orders["results"][0])

        by_method = self.client.get(base + "&method=cash").json()["data"]
        self.assertEqual(by_method["count"], 1)
        self.assertEqual(by_method["results"][0]["payment_method"], "cash")
        self.assertEqual(by_method["filters"]["method"], "cash")

        rc = self.client.get(
            base + "&collection_timing=rider_collected"
        ).json()["data"]
        self.assertEqual(rc["count"], 1)  # the cash order
        deferred = self.client.get(
            base + "&collection_timing=deferred"
        ).json()["data"]
        self.assertEqual(deferred["count"], 1)  # the postpaid order

    def test_cod_orders_drilldown(self):
        # setUp made exactly one COD order (cash, Done, 2000), no COD record yet
        base = "/api/ops/cod-dashboard/orders/?period=this_month"
        allc = self.client.get(base).json()["data"]
        self.assertEqual(allc["count"], 1)
        self.assertTrue(allc["results"][0]["collect_on_delivery"])
        self.assertIn("cod_records", allc["results"][0])

        by_merchant = self.client.get(base + "&merchant=TestMart").json()["data"]
        self.assertEqual(by_merchant["count"], 1)
        pending = self.client.get(base + "&cod_status=pending").json()["data"]
        self.assertEqual(pending["count"], 1)  # nothing remitted yet
        collected = self.client.get(base + "&cod_status=collected").json()["data"]
        self.assertEqual(collected["count"], 0)


# ---------------------------------------------------------------------------
# Fuel tracking — upload + dashboard
# ---------------------------------------------------------------------------


class FuelTests(OpsTestBase):
    def setUp(self):
        super().setUp()
        self.asset = self.make_asset("TST111", vehicle_type="bike")
        self.rider = Rider.objects.create(
            user=self.make_user(contact="FuelRider"), vehicle_asset=self.asset
        )
        self.today = timezone.localdate()
        self.when = datetime.combine(self.today, time(10, 0))

    def _upload(self, rows, client=None):
        client = client or self.client
        bio = make_fuel_xlsx(rows)
        return client.post(
            "/api/ops/fuel/upload/", {"file": bio}, format="multipart"
        )

    def test_upload_creates_and_links_by_plate(self):
        r = self._upload([
            fuel_row(1001, "TST111", 5000, 4.1, self.when),
            fuel_row(1002, "ZZZ999", 3000, 3.2, self.when),
        ])
        self.assertEqual(r.status_code, 200)
        s = r.json()["data"]
        self.assertEqual(s["created"], 2)
        self.assertIn("ZZZ999", s["unmatched_plates"])

        linked = FuelBill.objects.get(invoice_number="1001")
        self.assertEqual(linked.vehicle_asset_id, self.asset.id)
        self.assertEqual(linked.rider_id, self.rider.id)
        unmatched = FuelBill.objects.get(invoice_number="1002")
        self.assertIsNone(unmatched.vehicle_asset_id)

    def test_upload_is_idempotent(self):
        rows = [fuel_row(2001, "TST111", 5000, 4.1, self.when)]
        self._upload(rows)
        r2 = self._upload(rows)
        s2 = r2.json()["data"]
        self.assertEqual(s2["created"], 0)
        self.assertEqual(s2["updated"], 1)
        self.assertEqual(FuelBill.objects.count(), 1)

    def test_fuel_dashboard_stats(self):
        self._upload([
            fuel_row(3001, "TST111", 5000, 4.1, self.when),
            fuel_row(3002, "ZZZ999", 3000, 3.2, self.when),
        ])
        r = self.client.get(
            f"/api/ops/fuel-dashboard/?filter=single_date&date={self.today}"
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["summary"]["records"], 2)
        self.assertEqual(data["summary"]["total_cost"], "8000.00")
        self.assertEqual(data["summary"]["total_liters"], "7.300")
        self.assertEqual(len(data["daily_trend"]), 1)

    # Auth disabled on oprtn_dashboard views — scope no longer enforced.
    # def test_upload_requires_write_scope(self):
    #     raw = "sk_" + secrets.token_hex(24)
    #     ServiceAPIKey.objects.create(
    #         name="ro", prefix=raw[:11],
    #         key_hash=hashlib.sha256(raw.encode()).hexdigest(),
    #         scopes=["occ:read"], is_active=True,
    #     )
    #     ro = APIClient()
    #     ro.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
    #     r = self._upload(
    #         [fuel_row(4001, "TST111", 5000, 4.1, self.when)], client=ro
    #     )
    #     self.assertEqual(r.status_code, 403)

    def test_upload_rejects_non_xlsx(self):
        bad = BytesIO(b"not a spreadsheet")
        bad.name = "data.txt"
        r = self.client.post(
            "/api/ops/fuel/upload/", {"file": bad}, format="multipart"
        )
        self.assertEqual(r.status_code, 400)

    def test_upload_requires_file(self):
        r = self.client.post("/api/ops/fuel/upload/", {}, format="multipart")
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# General dashboard filter
# ---------------------------------------------------------------------------


class _StubRequest:
    def __init__(self, **query):
        self.query_params = query


class FilterTests(TestCase):
    def test_single_date(self):
        s, e, desc = parse_filter(
            _StubRequest(filter="single_date", date="2025-03-15")
        )
        self.assertEqual(desc["filter"], "single_date")
        self.assertEqual(s.date().isoformat(), "2025-03-15")
        self.assertEqual(e.date().isoformat(), "2025-03-15")

    def test_date_range(self):
        s, e, desc = parse_filter(
            _StubRequest(
                filter="date_range", start_date="2025-01-01",
                end_date="2025-01-31",
            )
        )
        self.assertEqual(desc["filter"], "date_range")
        self.assertEqual(s.date().isoformat(), "2025-01-01")
        self.assertEqual(e.date().isoformat(), "2025-01-31")

    def test_date_range_reversed_is_swapped(self):
        s, e, _ = parse_filter(
            _StubRequest(
                filter="date_range", start_date="2025-01-31",
                end_date="2025-01-01",
            )
        )
        self.assertLessEqual(s, e)
        self.assertEqual(s.date().isoformat(), "2025-01-01")

    def test_annually(self):
        s, _, desc = parse_filter(_StubRequest(filter="annually"))
        self.assertEqual(desc["filter"], "annually")
        self.assertEqual((s.month, s.day), (1, 1))
        self.assertEqual(s.year, timezone.localdate().year)

    def test_today(self):
        s, e, desc = parse_filter(_StubRequest(filter="today"))
        self.assertEqual(desc["filter"], "today")
        self.assertEqual(s.date(), timezone.localdate())


# ---------------------------------------------------------------------------
# Dashboard cache refresh task (every 30 min)
# ---------------------------------------------------------------------------


class CacheRefreshTests(OpsTestBase):
    def test_refresh_warms_cache_and_endpoint_serves_it(self):
        from dispatcher.periods import _parse_period

        from .caching import get_cached
        from .tasks import refresh_dashboard_cache

        m, v = self.make_user(), self.make_vehicle()
        self.make_order(m, v, 1000, "wallet", "Done")

        out = refresh_dashboard_cache()
        self.assertEqual(out["warmed"]["this_month"], "ok")

        # snapshot is cached for this_month payments
        s, e, _ = _parse_period("this_month")
        desc = {
            "filter": "this_month",
            "start": s.isoformat(),
            "end": e.isoformat(),
        }
        cached = get_cached("payments", desc)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["total_amount"], "1000.00")

        # endpoint serves the cached snapshot: delete the order, still returns 1000
        Order.objects.all().delete()
        r = self.client.get("/api/ops/payments/?filter=this_month")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["total_amount"], "1000.00")


# ---------------------------------------------------------------------------
# Consolidated order dashboard
# ---------------------------------------------------------------------------


class OrderDashboardTests(OpsTestBase):
    def test_order_dashboard_levels(self):
        m, v, rider = self.make_user(), self.make_vehicle(), self.make_rider()
        self.make_order(m, v, 1000, "wallet", "Done", rider=rider)
        self.make_order(m, v, 2000, "cash", "Done", rider=rider)
        self.make_order(m, v, 500, "wallet", "CustomerCanceled", rider=rider)
        self.make_order(m, v, 800, "wallet", "Started", rider=rider)

        data = self.client.get(
            "/api/ops/order-dashboard/?period=this_month"
        ).json()["data"]
        mg = data["management"]
        self.assertEqual(mg["total_orders"], 4)
        self.assertEqual(mg["delivered"], 2)
        self.assertEqual(mg["cancelled"], 1)
        self.assertEqual(mg["in_progress"], 1)
        self.assertEqual(mg["gross_revenue"], "3000.00")
        self.assertEqual(mg["avg_order_value"], "1500.00")
        self.assertEqual(mg["rider_commission_total"], "600.00")  # 3000 × 20%

        self.assertEqual(len(data["by_rider"]), 1)
        self.assertEqual(data["by_rider"][0]["delivered"], 2)
        self.assertEqual(data["by_rider"][0]["commission"], "600.00")
        self.assertEqual(len(data["by_merchant"]), 1)
        self.assertEqual(data["by_merchant"][0]["delivered"], 2)

    def test_order_orders_drilldown(self):
        m, v, rider = self.make_user(), self.make_vehicle(), self.make_rider()
        self.make_order(m, v, 1000, "wallet", "Done", rider=rider)
        self.make_order(m, v, 500, "wallet", "CustomerCanceled", rider=rider)
        base = "/api/ops/order-dashboard/orders/?period=this_month"

        allo = self.client.get(base).json()["data"]
        self.assertEqual(allo["count"], 2)
        self.assertIn("order_number", allo["results"][0])

        delivered = self.client.get(base + "&order_status=delivered").json()["data"]
        self.assertEqual(delivered["count"], 1)
        cancelled = self.client.get(base + "&order_status=cancelled").json()["data"]
        self.assertEqual(cancelled["count"], 1)
        by_rider = self.client.get(
            base + f"&rider={rider.rider_id}"
        ).json()["data"]
        self.assertEqual(by_rider["count"], 2)


# ---------------------------------------------------------------------------
# Live rider / vehicle tracking dashboard
# ---------------------------------------------------------------------------


class TrackingDashboardTests(OpsTestBase):
    def test_tracking_snapshot_and_linkage(self):
        now = timezone.now()
        a1 = self.make_asset(
            "TRK1", vehicle_type="bike", speed=20,
            engine_status="on", last_telemetry_at=now,
        )
        Rider.objects.create(
            user=self.make_user(contact="Mover"), vehicle_asset=a1,
            status="on_delivery", is_moving=True,
            current_latitude=Decimal("6.45"), current_longitude=Decimal("3.39"),
            current_speed=Decimal("20"), last_location_update=now,
        )
        a2 = self.make_asset(
            "TRK2", vehicle_type="bike", speed=0,
            engine_status="off", last_telemetry_at=now - timedelta(hours=5),
        )
        Rider.objects.create(
            user=self.make_user(contact="Resting"), vehicle_asset=a2,
            status="offline", is_moving=False,
            current_latitude=Decimal("6.46"), current_longitude=Decimal("3.40"),
            current_speed=Decimal("0"),
            last_location_update=now - timedelta(hours=5),
        )

        data = self.client.get("/api/ops/tracking-dashboard/").json()["data"]
        self.assertEqual(data["riders"]["total"], 2)
        self.assertEqual(data["riders"]["moving_now"], 1)
        self.assertEqual(data["riders"]["by_gps_status"]["moving"], 1)
        self.assertEqual(data["vehicles"]["moving_now"], 1)
        self.assertGreaterEqual(data["vehicles"]["offline"], 1)
        # live list carries the rider↔vehicle linkage
        plates = [
            it["vehicle"]["plate_number"] for it in data["live"] if it["vehicle"]
        ]
        self.assertIn("TRK1", plates)
