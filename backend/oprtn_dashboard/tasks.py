"""
Celery tasks for the Operations Dashboard app.

  - generate_alerts: run the alert engine. Wire onto CELERY_BEAT_SCHEDULE
    (~10 min for the full set; an optional ~2 min fast lane for
    BIKE_AFTER_HOURS / SPEED_VIOLATION / GHOST_RIDE). See guide §14.8.
"""

from celery import shared_task


@shared_task
def generate_alerts(only_types=None):
    """Evaluate enabled alert rules and reconcile alerts. Returns a summary."""
    from .alerts.engine import run_all_rules

    return run_all_rules(only_types=only_types)
