"""
OrderMetrics — status normalization + counts.

The single place the real `orders.Order` status enum is mapped to logical
buckets, so every dashboard agrees on what "delivered" / "cancelled" / etc. mean.

Real status enum (orders.Order.STATUS_CHOICES):
    Pending, Assigned, AssignmentAccepted, AssignmentRejected, Started,
    Pickup, Fulfilling, Arrived, Done, CustomerCanceled, RiderCanceled, Failed
"""

from django.db.models import Count, Q

# ── Canonical status groups ─────────────────────────────────────────
DELIVERED_STATUSES = ["Done"]
CANCELLED_STATUSES = ["CustomerCanceled", "RiderCanceled"]
FAILED_STATUSES = ["Failed"]
REJECTED_STATUSES = ["AssignmentRejected"]
PENDING_STATUSES = ["Pending"]
IN_PROGRESS_STATUSES = [
    "Assigned",
    "AssignmentAccepted",
    "Started",
    "Pickup",
    "Fulfilling",
    "Arrived",
]

# Terminal = no longer in flight.
TERMINAL_STATUSES = DELIVERED_STATUSES + CANCELLED_STATUSES + FAILED_STATUSES


def order_status_counts(qs):
    """Return all logical status-bucket counts in a single aggregate."""
    return qs.aggregate(
        total=Count("id"),
        delivered=Count("id", filter=Q(status__in=DELIVERED_STATUSES)),
        cancelled=Count("id", filter=Q(status__in=CANCELLED_STATUSES)),
        failed=Count("id", filter=Q(status__in=FAILED_STATUSES)),
        rejected=Count("id", filter=Q(status__in=REJECTED_STATUSES)),
        pending=Count("id", filter=Q(status__in=PENDING_STATUSES)),
        in_progress=Count("id", filter=Q(status__in=IN_PROGRESS_STATUSES)),
    )
