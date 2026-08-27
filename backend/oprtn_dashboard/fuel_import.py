"""
Fuel bills spreadsheet importer.

Parses the daily fuel bills .xlsx (see the canonical sample format) and upserts
one `FuelBill` per row, keyed by the unique "Invoice number". Columns are mapped
by header name (normalized) so column order/spacing changes don't break import.

The "Vehicle" column (plate number) is matched to a `dispatcher.VehicleAsset`
(case-insensitive) to attach the vehicle + its rider.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

# Normalized header text -> FuelBill field name.
HEADER_MAP = {
    "invoice number": "invoice_number",
    "branch": "branch",
    "vehicle": "vehicle_plate",
    "vehicle brand": "vehicle_brand",
    "vehicle model": "vehicle_model",
    "internal number": "internal_number",
    "trip number": "trip_number",
    "type of fuel": "fuel_type",
    "fuel price": "fuel_price",
    "cost": "cost",
    "worker tip": "worker_tip",
    # Newer exports rename "Worker tip" to "Service fees" (same charge).
    "service fees": "worker_tip",
    "km/l": "km_per_l",
    "l/100 km": "l_per_100km",
    "number of liters": "liters",
    "odometer": "odometer",
    "payment method": "payment_method",
    "delegate": "delegate",
    "the station": "station",
    "station branch": "station_branch",
    "governorate - city - district": "location_text",
    "station location": "station_location",
    "date": "bill_datetime",
}

DECIMAL_FIELDS = {
    "fuel_price", "cost", "worker_tip", "km_per_l",
    "l_per_100km", "liters", "odometer",
}
TEXT_FIELDS = {
    "branch", "vehicle_plate", "vehicle_brand", "vehicle_model",
    "internal_number", "trip_number", "fuel_type", "payment_method",
    "delegate", "station", "station_branch", "location_text",
    "station_location",
}


def _to_decimal(value):
    if value is None or value in ("", "-"):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y"):
            try:
                dt = datetime.strptime(str(value).strip(), fmt)
                break
            except ValueError:
                continue
        if dt is None:
            return None
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def import_fuel_workbook(file_obj):
    """Parse an uploaded .xlsx file-like object; upsert FuelBill rows."""
    import openpyxl

    from dispatcher.models import VehicleAsset
    from .models import FuelBill

    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)

    # Some exports prepend title/metadata rows before the real header row,
    # so scan the first few rows for the one containing "Invoice number".
    header = None
    col = {}
    for _ in range(10):
        try:
            candidate = next(rows)
        except StopIteration:
            break
        mapped = {}
        for i, h in enumerate(candidate):
            if h is None:
                continue
            field = HEADER_MAP.get(str(h).strip().lower())
            if field:
                mapped[field] = i
        if "invoice_number" in mapped:
            header = candidate
            col = mapped
            break
    if header is None:
        raise ValueError(
            "Unrecognized format: an 'Invoice number' column is required."
        )

    summary = {
        "total_rows": 0, "created": 0, "updated": 0, "skipped": 0,
        "unmatched_plates": set(),
        "date_from": None, "date_to": None,
    }

    def cell(row, field):
        i = col.get(field)
        return row[i] if i is not None and i < len(row) else None

    for row in rows:
        if row is None or all(c is None for c in row):
            continue
        summary["total_rows"] += 1

        invoice = cell(row, "invoice_number")
        if invoice in (None, "", "-"):
            summary["skipped"] += 1
            continue

        bill_dt = _to_datetime(cell(row, "bill_datetime"))
        if bill_dt is None:
            summary["skipped"] += 1
            continue

        bill_d = bill_dt.date()
        if summary["date_from"] is None or bill_d < summary["date_from"]:
            summary["date_from"] = bill_d
        if summary["date_to"] is None or bill_d > summary["date_to"]:
            summary["date_to"] = bill_d

        plate = _to_text(cell(row, "vehicle_plate"))
        asset = None
        rider = None
        if plate:
            asset = VehicleAsset.objects.filter(
                plate_number__iexact=plate
            ).first()
            if asset:
                rider = asset.riders.first()
            else:
                summary["unmatched_plates"].add(plate)

        defaults = {
            "vehicle_asset": asset,
            "rider": rider,
            "bill_datetime": bill_dt,
            "bill_date": bill_dt.date(),
            "raw": {
                str(k): (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in zip(header, row)
                if k is not None
            },
        }
        for field in TEXT_FIELDS:
            if field in col:
                defaults[field] = _to_text(cell(row, field))
        for field in DECIMAL_FIELDS:
            if field in col:
                val = _to_decimal(cell(row, field))
                if field == "odometer":
                    defaults[field] = val
                else:
                    defaults[field] = val if val is not None else Decimal("0")

        _, created = FuelBill.objects.update_or_create(
            invoice_number=str(invoice), defaults=defaults
        )
        summary["created" if created else "updated"] += 1

    summary["unmatched_plates"] = sorted(summary["unmatched_plates"])
    if summary["date_from"] is not None:
        summary["date_from"] = summary["date_from"].isoformat()
    if summary["date_to"] is not None:
        summary["date_to"] = summary["date_to"].isoformat()
    return summary
