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

    # Select the tier by distance and apply rate × distance directly
    for tier in tiers:
        if not isinstance(tier, dict):
            continue

        rate = float(tier.get("rate") or 0)
        max_km = tier.get("max_km")

        # Unbounded tier (or missing max) applies to any remaining distances
        if max_km is None or km <= float(max_km):
            return _money(round(km * rate))

    # Fallback for unexpected tier config
    last_rate = float(tiers[-1].get("rate") or 0) if tiers else 0
    return _money(round(km * last_rate))


def calculate_effective_fare(
    merchant_user: Optional[object],
    vehicle: object,
    distance_km: Any,
    duration_minutes: Any,
    return_metadata: bool = False,
) -> Any:
    """Return fare using manual price lists, overrides, or base calculation.

    Precedence (when is_active=True):
      1) MerchantPriceList (bucket match)
      2) MerchantPricingOverride.flat_fee
      3) MerchantPricingOverride.pricing_tiers
      4) vehicle.calculate_fare()
    """

    # Avoid importing Django models at module import time
    from .models import MerchantPricingOverride, MerchantPriceList

    fare = None
    source = "base"
    label = None

    if merchant_user and getattr(merchant_user, "id", None):
        # 1. Check for manual Price List (highest priority)
        price_list = (
            MerchantPriceList.objects.filter(
                merchant_id=merchant_user.id,
                vehicle_id=getattr(vehicle, "id", None),
                is_active=True,
            )
            .prefetch_related("items")
            .first()
        )

        if price_list:
            km = Decimal(str(distance_km or 0))
            # Find a bucket that covers this distance
            bucket = price_list.items.filter(min_km__lte=km, max_km__gte=km).first()
            if bucket:
                fare = _money(bucket.fixed_fee)
                source = "manual_list"
                label = bucket.label

        # 2. Check for traditional Merchant Override
        if fare is None:
            override = (
                MerchantPricingOverride.objects.filter(
                    merchant_id=merchant_user.id,
                    vehicle_id=getattr(vehicle, "id", None),
                    is_active=True,
                )
                .order_by("-updated_at")
                .first()
            )

            if override:
                if override.flat_fee is not None:
                    fare = _money(override.flat_fee)
                    source = "override_flat"
                elif override.pricing_tiers and isinstance(override.pricing_tiers, dict):
                    try:
                        fare = calculate_tiered_fare(
                            distance_km or 0, override.pricing_tiers
                        )
                        source = "override_tiered"
                    except Exception:
                        pass

    # 3. Fallback to basic vehicle calculation
    if fare is None:
        fare = vehicle.calculate_fare(distance_km or 0, duration_minutes or 0)

    if return_metadata:
        return {
            "fare": fare,
            "source": source,
            "label": label,
        }

    return fare
