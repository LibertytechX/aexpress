"""
General dashboard date filter — applied across every ops metrics section.

Supported `?filter=` values:
    today, this_week, this_month, annually, single_date, date_range

  - single_date : also pass ?date=YYYY-MM-DD
  - date_range  : also pass ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

`parse_filter(request)` returns (start_dt, end_dt, descriptor) — timezone-aware
datetimes plus a descriptor dict for the response envelope's `date_range`. Each
endpoint applies (start_dt, end_dt) to its own date field (Order.created_at,
Alert.created_at, FuelBill.bill_date, ...).

Standard buckets reuse `dispatcher.periods._parse_period` so the math is shared.
"""

from datetime import datetime, time

from django.utils import timezone

from dispatcher.periods import _parse_period

SUPPORTED_FILTERS = [
    "today",
    "this_week",
    "this_month",
    "annually",
    "single_date",
    "date_range",
]


def _aware(dt):
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_filter(request):
    """Return (start_dt, end_dt, descriptor) for the requested filter."""
    params = request.query_params
    f = params.get("filter") or params.get("period") or "this_month"
    today = timezone.localdate()

    if f in ("annually", "yearly", "annual", "this_year"):
        start, end, _ = _parse_period("this_year")
        return start, end, {
            "filter": "annually",
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

    if f == "single_date":
        try:
            d = _parse_date(params.get("date"))
        except (TypeError, ValueError):
            d = today
        start = _aware(datetime.combine(d, time.min))
        end = _aware(datetime.combine(d, time.max))
        return start, end, {
            "filter": "single_date",
            "date": d.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

    if f == "date_range":
        try:
            s = _parse_date(params.get("start_date"))
        except (TypeError, ValueError):
            s = today
        try:
            e = _parse_date(params.get("end_date"))
        except (TypeError, ValueError):
            e = today
        if e < s:
            s, e = e, s
        start = _aware(datetime.combine(s, time.min))
        end = _aware(datetime.combine(e, time.max))
        return start, end, {
            "filter": "date_range",
            "start_date": s.isoformat(),
            "end_date": e.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

    # Standard buckets: today / this_week / this_month (+ any _parse_period value)
    start, end, _ = _parse_period(f)
    return start, end, {
        "filter": f,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
