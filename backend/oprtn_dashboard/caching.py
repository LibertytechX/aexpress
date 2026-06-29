"""
Dashboard read-through cache for the heavy metric endpoints.

The periodic task (`tasks.refresh_dashboard_cache`) pre-computes payments / COD /
fuel payloads for the common filters every 30 min; endpoints serve from cache
when warm and fall back to a live compute (caching the result) on a miss.

Cache keys use **date granularity** (not the volatile `end=now` timestamp) so a
filter's key is stable across a day and the pre-warmed snapshot actually hits.
"""

from django.conf import settings
from django.core.cache import cache

# TTL ~ the refresh cadence so a warm snapshot never goes far stale.
DEFAULT_TTL = getattr(settings, "OPS_DASHBOARD_CACHE_TTL", 1800)  # 30 min


def cache_key(name, descriptor):
    """Stable per-day key from the filter descriptor produced by parse_filter."""
    d = descriptor or {}
    start = str(d.get("start", ""))[:10]
    end = str(d.get("end", ""))[:10]
    return f"ops:dash:{name}:{d.get('filter')}:{start}:{end}"


def get_cached(name, descriptor):
    """Cache read that degrades gracefully if the cache backend is unreachable."""
    try:
        return cache.get(cache_key(name, descriptor))
    except Exception:  # noqa: BLE001 — never let cache outages break reads
        return None


def set_cached(name, descriptor, data, ttl=None):
    """Cache write that is best-effort (returns data regardless of outcome)."""
    try:
        cache.set(cache_key(name, descriptor), data, ttl or DEFAULT_TTL)
    except Exception:  # noqa: BLE001
        pass
    return data
