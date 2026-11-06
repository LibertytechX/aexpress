"""
Shared period / date-range helpers for analytics endpoints.

Extracted from ``dispatcher.occ_views`` so both the OCC views and the
``oprtn_dashboard`` app compute periods identically. All datetimes are
timezone-aware (Africa/Lagos).
"""

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.utils import timezone


def _parse_period(period_str):
    """
    Return (start_dt, end_dt, is_fully_elapsed) for the requested period.
    All datetimes are timezone-aware (Africa/Lagos).
    """
    now = timezone.now()
    today = now.date()

    if period_str == "today":
        start = datetime.combine(today, time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "yesterday":
        yesterday = today - timedelta(days=1)
        start = datetime.combine(yesterday, time.min)
        end = datetime.combine(yesterday, time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True

    if period_str == "this_week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "past_7_days":
        start = datetime.combine(today - timedelta(days=7), time.min)
        end = now
        return timezone.make_aware(start), end, True

    if period_str == "this_month":
        start = datetime.combine(today.replace(day=1), time.min)
        end = now
        return timezone.make_aware(start), end, False

    if period_str == "last_month":
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        start = datetime.combine(last_month_end.replace(day=1), time.min)
        end = datetime.combine(last_month_end, time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True

    if period_str == "this_year":
        start = datetime.combine(date(today.year, 1, 1), time.min)
        end = now
        return timezone.make_aware(start), end, False

    # YYYY-MM format
    try:
        parts = period_str.split("-")
        year, month = int(parts[0]), int(parts[1])
        last_day = calendar.monthrange(year, month)[1]
        start = datetime.combine(date(year, month, 1), time.min)
        end = datetime.combine(date(year, month, last_day), time.max)
        return timezone.make_aware(start), timezone.make_aware(end), True
    except (ValueError, IndexError):
        pass

    # Default to this_month
    start = datetime.combine(today.replace(day=1), time.min)
    end = now
    return timezone.make_aware(start), end, False


def _scale_target(full_monthly, period_str):
    """Scale a monthly target to the requested period."""
    now = timezone.now()
    today = now.date()

    if period_str == "today":
        return full_monthly / Decimal("26")
    if period_str == "yesterday":
        return full_monthly / Decimal("26")
    if period_str == "this_week":
        days_in = today.weekday() + 1
        return full_monthly / Decimal("26") * Decimal(str(days_in))
    if period_str == "past_7_days":
        return full_monthly / Decimal("26") * Decimal("7")
    if period_str in ("this_month", "last_month"):
        return full_monthly
    if period_str == "this_year":
        return full_monthly * Decimal(str(today.month))
    return full_monthly
