"""
Management command: sync_bike_telemetry

Fetches live device data from the Concept Nova tracking API and upserts
telemetry into VehicleAsset records, creating new assets where needed.

Usage:
    python manage.py sync_bike_telemetry
    python manage.py sync_bike_telemetry --dry-run
"""

import logging
import os
from datetime import timedelta, timezone as dt_timezone

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dispatcher.models import VehicleAsset

logger = logging.getLogger(__name__)

CONCEPT_NOVA_BASE_URL = os.environ.get(
    "CONCEPT_NOVA_BASE_URL", "https://monitor.concept-nova.com"
)
CONCEPT_NOVA_EMAIL = os.environ.get("CONCEPT_NOVA_EMAIL", "")
CONCEPT_NOVA_PASSWORD = os.environ.get("CONCEPT_NOVA_PASSWORD", "")

REQUEST_TIMEOUT = 15  # seconds
DEVICE_FETCH_LIMIT = 500


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _login() -> str:
    """
    Authenticate with Concept Nova and return the user_api_hash token.
    Raises RuntimeError on any failure so the caller can log and abort.
    """
    url = f"{CONCEPT_NOVA_BASE_URL}/api/login"
    try:
        response = requests.post(
            url,
            data={"email": CONCEPT_NOVA_EMAIL, "password": CONCEPT_NOVA_PASSWORD},
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Login request timed out after %ss" % REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("Login HTTP error: %s" % exc)

    try:
        result = response.json()
    except ValueError:
        raise RuntimeError("Login response was not valid JSON")

    token = result.get("user_api_hash")
    if not token:
        raise RuntimeError(
            "Login succeeded but response missing 'user_api_hash'. "
            "Response keys: %s" % list(result.keys())
        )
    return token


def _fetch_devices(token: str) -> tuple[list, int, str]:
    """
    Fetch all devices from Concept Nova.
    Returns (devices_list, http_status_code, raw_response_snippet).
    """
    url = f"{CONCEPT_NOVA_BASE_URL}/api/get_devices"
    params = {"lang": "en", "user_api_hash": token, "limit": DEVICE_FETCH_LIMIT}
    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("get_devices request timed out after %ss" % REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("get_devices HTTP error: %s" % exc)

    raw_text = response.text
    snippet = raw_text[:50]
    status_code = response.status_code

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("get_devices response was not valid JSON. Snippet: %s" % snippet)

    # API returns a list of group objects, each with an 'items' list
    devices = []
    for group in data:
        devices.extend(group.get("items", []))

    return devices, status_code, snippet


# ---------------------------------------------------------------------------
# Data normalisation helpers
# ---------------------------------------------------------------------------

def _normalise_engine_status(raw) -> str:
    if raw is None:
        return VehicleAsset.EngineStatus.UNKNOWN
    mapping = {
        "on": VehicleAsset.EngineStatus.ON,
        "off": VehicleAsset.EngineStatus.OFF,
        "idle": VehicleAsset.EngineStatus.IDLE,
    }
    return mapping.get(str(raw).lower(), VehicleAsset.EngineStatus.UNKNOWN)


def _normalise_stop_duration(raw) -> timedelta | None:
    """Accept seconds (int/float) or None."""
    if raw is None:
        return None
    try:
        return timedelta(seconds=float(raw))
    except (TypeError, ValueError):
        return None


def _normalise_moved_timestamp(raw):
    """Accept Unix epoch (int/float) or None."""
    if raw is None:
        return None
    try:
        from datetime import datetime
        return datetime.fromtimestamp(float(raw), tz=dt_timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def _upsert_device(device: dict, status_code: int, snippet: str, dry_run: bool) -> str:
    """
    Upsert a single device dict into VehicleAsset.
    Returns 'created', 'updated', or 'skipped'.
    """
    provider_id = str(device.get("id", "")).strip()
    if not provider_id:
        logger.warning("Device entry has no 'id' field — skipping: %s", device)
        return "skipped"

    device_name = (device.get("name") or "").strip()
    is_online = bool(device.get("online"))
    lat = device.get("lat")
    lng = device.get("lng")

    telemetry_fields = {
        "latitude": lat,
        "longitude": lng,
        "speed": device.get("speed") or 0,
        "course": device.get("course"),
        "engine_status": _normalise_engine_status(device.get("engine_status")),
        "stop_duration": _normalise_stop_duration(device.get("stop_duration")),
        "moved_timestamp": _normalise_moved_timestamp(device.get("moved_timestamp")),
        "last_telemetry_at": timezone.now(),
        "is_active": is_online,
        "sync_meta": {
            "response_code": status_code,
            "response_snippet": snippet,
            "synced_at": timezone.now().isoformat(),
        },
    }

    existing = VehicleAsset.objects.filter(provider_id=provider_id).first()

    if existing:
        if not dry_run:
            for field, value in telemetry_fields.items():
                setattr(existing, field, value)
            existing.save(update_fields=list(telemetry_fields.keys()))
        logger.debug("Updated  provider_id=%s  name=%s", provider_id, device_name)
        return "updated"

    # New device — create a minimal VehicleAsset record.
    # plate_number must be unique; use the device name as a provisional value.
    # Dispatchers can edit the plate via the portal after creation.
    provisional_plate = (device_name or f"SYNC-{provider_id}")[:20]
    if VehicleAsset.objects.filter(plate_number=provisional_plate).exists():
        provisional_plate = f"{provisional_plate[:14]}-{provider_id[:5]}"

    create_defaults = {
        "plate_number": provisional_plate,
        "vehicle_type": VehicleAsset.VehicleType.BIKE,
        "make": "",
        "model": "",
        **telemetry_fields,
    }

    if not dry_run:
        VehicleAsset.objects.create(provider_id=provider_id, **create_defaults)

    logger.debug("Created  provider_id=%s  plate=%s", provider_id, provisional_plate)
    return "created"


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Fetch live bike/device data from Concept Nova tracking API and "
        "upsert telemetry into VehicleAsset records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Fetch data and log what would happen without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes will occur."))

        # Validate env vars before hitting the network
        if not CONCEPT_NOVA_EMAIL or not CONCEPT_NOVA_PASSWORD:
            self.stderr.write(
                self.style.ERROR(
                    "CONCEPT_NOVA_EMAIL and CONCEPT_NOVA_PASSWORD must be set in the "
                    "environment (check /home/backend/.env on the server)."
                )
            )
            return

        # ── Step 1: authenticate ────────────────────────────────────
        self.stdout.write("Logging in to Concept Nova API…")
        try:
            token = _login()
        except RuntimeError as exc:
            logger.error("sync_bike_telemetry: login failed — %s", exc)
            self.stderr.write(self.style.ERROR("Login failed: %s" % exc))
            return
        self.stdout.write(self.style.SUCCESS("Authenticated OK"))

        # ── Step 2: fetch devices ───────────────────────────────────
        self.stdout.write("Fetching devices…")
        try:
            devices, status_code, snippet = _fetch_devices(token)
        except RuntimeError as exc:
            logger.error("sync_bike_telemetry: fetch failed — %s", exc)
            self.stderr.write(self.style.ERROR("Fetch failed: %s" % exc))
            return

        self.stdout.write("Received %d device(s) from API" % len(devices))
        logger.info("sync_bike_telemetry: received %d device(s)", len(devices))

        # ── Step 3: upsert ──────────────────────────────────────────
        counts = {"created": 0, "updated": 0, "skipped": 0}
        try:
            with transaction.atomic():
                for device in devices:
                    result = _upsert_device(device, status_code, snippet, dry_run)
                    counts[result] += 1
        except Exception as exc:
            logger.exception("sync_bike_telemetry: database error during upsert")
            self.stderr.write(self.style.ERROR("Database error: %s" % exc))
            return

        # ── Step 4: report ──────────────────────────────────────────
        summary = (
            "Sync complete — created: %(created)d  updated: %(updated)d  skipped: %(skipped)d"
            % counts
        )
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info("sync_bike_telemetry: %s", summary)


