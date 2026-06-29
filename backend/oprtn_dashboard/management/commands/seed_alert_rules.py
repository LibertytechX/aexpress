"""
Seed default AlertRule rows (idempotent).

Creates one rule per AlertType with sensible default thresholds, so the alert
engine (later phase) reads all numbers from the DB rather than hardcoding them.
Existing rules are left untouched unless --reset is passed.

Usage:
    python manage.py seed_alert_rules
    python manage.py seed_alert_rules --reset    # overwrite existing rule config
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from oprtn_dashboard.models import AlertRule, AlertType, Severity

D = Decimal

# alert_type -> default config. Keys map to AlertRule fields; `params` is JSON.
DEFAULTS = {
    # ── Rider integrity / behaviour ──────────────────────────────────
    AlertType.BIKE_AFTER_HOURS: {
        "default_severity": Severity.HIGH,
        "window_minutes": 10,
        "params": {
            "curfew_start_hour": 20,  # 8pm — end of work period
            "curfew_end_hour": 6,  # back on at 6am
            "vehicle_types": ["bike"],
            "min_speed_kmh": 5,
        },
        "description": "Bike moving between 20:00 and 06:00.",
    },
    AlertType.GHOST_RIDE: {
        "default_severity": Severity.CRITICAL,
        "window_minutes": 15,
        "params": {"min_speed_kmh": 5},
        "description": "Rider offline but assigned vehicle is moving.",
    },
    AlertType.RIDER_IDLE: {
        "default_severity": Severity.MEDIUM,
        "window_minutes": 60,
        "params": {},
        "description": "Online rider stationary beyond the window.",
    },
    AlertType.SPEED_VIOLATION: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("80"),
        "critical_threshold": D("120"),
        "params": {"unit": "kmh"},
        "description": "Speed over 80 (high) / 120 (critical) km/h.",
    },
    AlertType.LOW_ACCEPTANCE: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("70"),
        "critical_threshold": D("50"),
        "params": {"min_offers": 5, "comparison": "below_pct"},
        "description": "Acceptance rate below 70% (warn) / 50% (critical).",
    },
    AlertType.RIDER_INACTIVITY: {
        "default_severity": Severity.MEDIUM,
        "window_minutes": 480,  # 8h online with 0 orders
        "params": {"min_online_minutes": 480},
        "description": "Online 8h+ with zero completed orders.",
    },
    AlertType.LOW_CSAT: {
        "default_severity": Severity.MEDIUM,
        "warn_threshold": D("3.5"),
        "critical_threshold": D("3.0"),
        "params": {"min_ratings": 3, "comparison": "below"},
        "description": "Average CSAT below 3.5 (warn) / 3.0 (critical).",
    },
    # ── Order lifecycle ──────────────────────────────────────────────
    AlertType.INCOMPLETE_ORDER: {
        "default_severity": Severity.HIGH,
        "window_minutes": 360,  # accepted but not Done after 6h
        "params": {
            "accepted_statuses": [
                "AssignmentAccepted",
                "Started",
                "Pickup",
                "Fulfilling",
                "Arrived",
            ]
        },
        "description": "Rider accepted but order not Done within 6h.",
    },
    AlertType.ORDER_STUCK: {
        "default_severity": Severity.MEDIUM,
        "window_minutes": 240,  # Pending/Assigned >= 4h
        "params": {"statuses": ["Pending", "Assigned"]},
        "description": "Pending/Assigned for 4h+ (never started).",
    },
    AlertType.ORDER_DELAYED: {
        "default_severity": Severity.MEDIUM,
        "window_minutes": 360,  # in transit >= 6h
        "params": {"statuses": ["Started", "Pickup", "Fulfilling", "Arrived"]},
        "description": "In transit for 6h+.",
    },
    AlertType.HIGH_CANCELLATION: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("20"),
        "critical_threshold": D("30"),
        "params": {"min_orders": 5, "window_hours": 24},
        "description": "Cancellation rate over 20% (warn) / 30% (critical).",
    },
    AlertType.RELAY_ROUTING_FAILURE: {
        "default_severity": Severity.HIGH,
        "params": {},
        "description": "Relay order routing_status = failed.",
    },
    # ── Financial / COD ──────────────────────────────────────────────
    AlertType.COD_RETENTION: {
        "default_severity": Severity.HIGH,
        "params": {"warn_hours": 24, "critical_hours": 48},
        "description": "Delivered COD unremitted 24h+ (warn) / 48h+ (crit).",
    },
    AlertType.COD_GAP: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("20"),
        "critical_threshold": D("40"),
        "params": {"comparison": "above_pct"},
        "description": "Uncollected COD over 20% (warn) / 40% (critical).",
    },
    AlertType.COD_FEE_LEAKAGE: {
        "default_severity": Severity.MEDIUM,
        "params": {},
        "description": "Delivered COD order with no COD fee captured.",
    },
    AlertType.PAYMENT_FAILURE_SPIKE: {
        "default_severity": Severity.MEDIUM,
        "warn_threshold": D("10"),
        "critical_threshold": D("25"),
        "window_minutes": 60,
        "params": {},
        "description": "Failed payments per hour over 10 (warn) / 25 (crit).",
    },
    AlertType.HIGH_RIDER_PAYOUT: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("70"),
        "critical_threshold": D("85"),
        "params": {"comparison": "above_pct"},
        "description": "Rider payout over 70% (warn) / 85% (crit) of revenue.",
    },
    AlertType.REVENUE_DROP: {
        "default_severity": Severity.HIGH,
        "warn_threshold": D("30"),
        "critical_threshold": D("50"),
        "params": {"comparison": "drop_pct"},
        "description": "Revenue down 30% (warn) / 50% (crit) vs prev period.",
    },
    # ── Fleet / compliance / system ──────────────────────────────────
    AlertType.INSURANCE_EXPIRING: {
        "default_severity": Severity.MEDIUM,
        "params": {"warn_days": 60, "critical_days": 30},
        "description": "Insurance expiring within 60 (warn) / 30 (crit) days.",
    },
    AlertType.REGISTRATION_EXPIRING: {
        "default_severity": Severity.MEDIUM,
        "params": {"warn_days": 60, "critical_days": 30},
        "description": "Registration expiring within 60/30 days.",
    },
    AlertType.ROADWORTHINESS_EXPIRING: {
        "default_severity": Severity.MEDIUM,
        "params": {"warn_days": 60, "critical_days": 30},
        "description": "Road-worthiness expiring within 60/30 days.",
    },
    AlertType.GPS_OFFLINE: {
        "default_severity": Severity.MEDIUM,
        "window_minutes": 120,  # no telemetry >= 2h
        "params": {},
        "description": "No telemetry for 2h+.",
    },
    AlertType.SYNC_FAILURE: {
        "default_severity": Severity.HIGH,
        "params": {},
        "description": "Telemetry sync errored (VehicleAsset.sync_meta).",
    },
    AlertType.WEBHOOK_FAILURE: {
        "default_severity": Severity.MEDIUM,
        "warn_threshold": D("10"),
        "window_minutes": 60,
        "params": {},
        "description": "10+ webhook failures in an hour.",
    },
}


class Command(BaseCommand):
    help = "Seed default AlertRule rows (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite config of existing rules with the defaults.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        created, updated, skipped = 0, 0, 0

        for alert_type, cfg in DEFAULTS.items():
            defaults = {
                "is_enabled": True,
                "default_severity": cfg.get("default_severity", Severity.MEDIUM),
                "warn_threshold": cfg.get("warn_threshold"),
                "critical_threshold": cfg.get("critical_threshold"),
                "window_minutes": cfg.get("window_minutes"),
                "params": cfg.get("params", {}),
                "description": cfg.get("description", ""),
            }
            obj, was_created = AlertRule.objects.get_or_create(
                alert_type=alert_type, defaults=defaults
            )
            if was_created:
                created += 1
            elif reset:
                for field, val in defaults.items():
                    setattr(obj, field, val)
                obj.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"AlertRules — created: {created}, "
                f"updated: {updated}, skipped: {skipped}"
            )
        )
