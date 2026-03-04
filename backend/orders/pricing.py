"""Pricing helpers.

Centralizes merchant-level override selection so all quote/order flows stay
consistent.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def calculate_tiered_fare(distance_km: Any, pricing_tiers: dict) -> Decimal:
    """Mirror Vehicle.calculate_fare() tiered branch but for an explicit config."""

    km = float(distance_km or 0)
    pt = pricing_tiers or {}

    if pt.get("type") != "tiered":
        raise ValueError("pricing_tiers.type must be 'tiered'")

    floor_km = float(pt.get("floor_km", 0) or 0)
    floor_fee = float(pt.get("floor_fee", 0) or 0)
    tiers = pt.get("tiers") or []

    if km <= floor_km:
        return _money(floor_fee)

    prev_max_km = floor_km
    prev_rate = None
    for i, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            continue

        rate = float(tier.get("rate") or 0)
        max_km = tier.get("max_km")

        min_floor = floor_fee if i == 0 else round(prev_max_km * float(prev_rate or 0))

        # Unbounded tier (or missing max) applies to any remaining distances
        if max_km is None or km <= float(max_km):
            price = max(round(km * rate), round(min_floor))
            return _money(price)

        prev_max_km = float(max_km)
        prev_rate = rate

    # Fallback for unexpected tier config
    last_rate = float(tiers[-1].get("rate") or 0) if tiers else 0
    min_floor = floor_fee if prev_rate is None else round(prev_max_km * float(prev_rate or 0))
    return _money(max(round(km * last_rate), round(min_floor)))


def calculate_effective_fare(
    merchant_user: Optional[object],
    vehicle: object,
    distance_km: Any,
    duration_minutes: Any,
) -> Decimal:
    """Return fare using (merchant, vehicle) override if present.

    Precedence (when is_active=True):
      1) flat_fee (if not null)
      2) pricing_tiers (if present and type=='tiered')
      3) vehicle.calculate_fare()
    """

    # Avoid importing Django models at module import time in case this file is
    # imported early during app loading.
    from .models import MerchantPricingOverride

    if not merchant_user or not getattr(merchant_user, "id", None):
        return vehicle.calculate_fare(distance_km or 0, duration_minutes or 0)

    override = (
        MerchantPricingOverride.objects.filter(
            merchant_id=merchant_user.id,
            vehicle_id=getattr(vehicle, "id", None),
            is_active=True,
        )
        .order_by("-updated_at")
        .first()
    )

    if not override:
        return vehicle.calculate_fare(distance_km or 0, duration_minutes or 0)

    # flat_fee can be 0, so we must check against None.
    if override.flat_fee is not None:
        return _money(override.flat_fee)

    if override.pricing_tiers and isinstance(override.pricing_tiers, dict):
        try:
            return calculate_tiered_fare(distance_km or 0, override.pricing_tiers)
        except Exception:
            # Fall through to global vehicle fare.
            pass

    return vehicle.calculate_fare(distance_km or 0, duration_minutes or 0)
