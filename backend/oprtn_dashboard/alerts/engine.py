"""
Alert engine — reconciles each rule's current firing set against open alerts.

For every enabled rule with a registered evaluator:
  1. compute the current firing candidates (rules.py),
  2. **upsert** by ``dedupe_key`` — refresh the open alert if one exists, else
     create a new one (status NEW),
  3. **auto-resolve** any open alert of that type whose key is no longer firing.

This delivers "one open record per ongoing issue" + auto-resolve. The DB-level
partial unique constraint (uniq_open_alert_per_dedupe_key) is the safety net
against concurrent duplicate creates.
"""

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from oprtn_dashboard.models import OPEN_ALERT_STATUSES, Alert, AlertRule

from .rules import RULE_EVALUATORS

logger = logging.getLogger(__name__)

_SUBJECT_FIELDS = ("rider", "order", "merchant", "vehicle", "zone")


def _alert_kwargs(c):
    """Build Alert field kwargs from a candidate dict."""
    kwargs = {
        "alert_type": c["alert_type"],
        "severity": c["severity"],
        "entity_type": c["entity_type"],
        "title": c["title"],
        "description": c.get("description", ""),
        "value": c.get("value"),
        "context": c.get("context", {}),
        "dedupe_key": c["dedupe_key"],
    }
    for field in _SUBJECT_FIELDS:
        kwargs[field] = c.get(field)
    return kwargs


def _reconcile(alert_type, candidates, summary):
    now = timezone.now()
    cand_by_key = {c["dedupe_key"]: c for c in candidates}

    open_alerts = Alert.objects.filter(
        alert_type=alert_type, status__in=OPEN_ALERT_STATUSES
    )
    open_by_key = {a.dedupe_key: a for a in open_alerts}

    # Upsert firing candidates.
    for key, c in cand_by_key.items():
        existing = open_by_key.get(key)
        if existing:
            existing.severity = c["severity"]
            existing.value = c.get("value")
            existing.context = c.get("context", {})
            existing.title = c["title"]
            existing.description = c.get("description", "")
            existing.last_seen_at = now
            for field in _SUBJECT_FIELDS:
                setattr(existing, field, c.get(field))
            existing.save()
            summary["updated"] += 1
        else:
            kwargs = _alert_kwargs(c)
            kwargs["first_seen_at"] = now
            kwargs["last_seen_at"] = now
            try:
                with transaction.atomic():
                    Alert.objects.create(**kwargs)
                summary["created"] += 1
            except IntegrityError:
                # A concurrent run already opened this issue — treat as update.
                logger.info("Alert %s already open (dedupe race)", key)
                summary["skipped"] += 1

    # Auto-resolve open alerts no longer firing.
    for key, alert in open_by_key.items():
        if key not in cand_by_key:
            alert.resolve(note="auto: condition cleared")
            summary["resolved"] += 1


def run_all_rules(only_types=None):
    """
    Evaluate enabled rules and reconcile alerts.

    only_types: optional iterable of alert_type values to limit the run.
    Returns a summary dict.
    """
    summary = {
        "evaluated": 0,
        "created": 0,
        "updated": 0,
        "resolved": 0,
        "skipped": 0,
        "no_evaluator": [],
    }

    rules = AlertRule.objects.filter(is_enabled=True)
    if only_types:
        rules = rules.filter(alert_type__in=list(only_types))

    for rule in rules:
        evaluator = RULE_EVALUATORS.get(rule.alert_type)
        if evaluator is None:
            summary["no_evaluator"].append(rule.alert_type)
            continue
        try:
            candidates = evaluator(rule)
        except Exception:  # noqa: BLE001 — one bad rule shouldn't kill the run
            logger.exception("Alert rule %s failed", rule.alert_type)
            continue
        summary["evaluated"] += 1
        _reconcile(rule.alert_type, candidates, summary)

    return summary
