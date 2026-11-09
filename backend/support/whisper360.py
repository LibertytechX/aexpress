"""
Whisper360 Support desk sync for rider tickets.

A rider's ticket is pushed to Whisper360 (POST /v1/support/tickets) as soon as
it is saved, and ops work it on the Whisper360 Support desk. Whisper360 owns
the ticket from then on: when an agent replies or changes the status, it calls
our webhook, and we read the ticket back (GET /v1/support/tickets/<id>) to copy
its status and the agent's latest reply into `status` and `resolution_note`,
which the rider app already shows.

Nothing here may fail a rider's request. A push that cannot reach Whisper360
leaves the ticket "failed"; `manage.py sync_whisper360_tickets` retries it.
"""

import hashlib
import hmac
import logging
import time

import httpx
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import SupportTicket

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(8.0, connect=3.0)
# A signed webhook older than this is refused, so a captured one cannot be replayed.
SIGNATURE_TOLERANCE_SECONDS = 300

PRIORITY_TO_WHISPER = {
    SupportTicket.Priority.LOW: "low",
    SupportTicket.Priority.MEDIUM: "normal",
    SupportTicket.Priority.HIGH: "high",
}

# Whisper360 ticket status -> the status the rider app shows.
STATUS_FROM_WHISPER = {
    "new": SupportTicket.Status.OPEN,
    "open": SupportTicket.Status.OPEN,
    "pending": SupportTicket.Status.IN_PROGRESS,
    "waiting_on_customer": SupportTicket.Status.IN_PROGRESS,
    "snoozed": SupportTicket.Status.IN_PROGRESS,
    "resolved": SupportTicket.Status.RESOLVED,
    "closed": SupportTicket.Status.CLOSED,
}


class Whisper360Error(Exception):
    """Whisper360 could not be reached, or refused the request."""


def is_enabled():
    return bool(settings.WHISPER360_API_URL and settings.WHISPER360_API_KEY)


def _headers():
    return {"Authorization": f"Bearer {settings.WHISPER360_API_KEY}"}


def _payload(ticket):
    rider = ticket.rider
    user = rider.user
    details = {
        "Reference": ticket.reference,
        "Category": ticket.get_category_display(),
        "Rider ID": rider.rider_id,
        "Phone": user.phone,
    }
    if ticket.order_id:
        details["Order"] = ticket.order.order_number
    payload = {
        # Our own ticket id: Whisper360 opens one ticket per id, so a retry is safe.
        "external_id": str(ticket.id),
        "user_id": str(rider.id),
        "name": user.get_full_name() or user.phone or rider.rider_id,
        "subject": ticket.subject,
        "description": ticket.message,
        "priority": PRIORITY_TO_WHISPER.get(ticket.priority, "normal"),
        "details": {k: v for k, v in details.items() if v},
        "occurred_at": ticket.created_at.isoformat(),
    }
    if settings.WHISPER360_SUPPORT_QUEUE_ID:
        payload["queue_id"] = settings.WHISPER360_SUPPORT_QUEUE_ID
    return payload


def _request(method, path, **kwargs):
    url = f"{settings.WHISPER360_API_URL}{path}"
    try:
        response = httpx.request(method, url, headers=_headers(), timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        raise Whisper360Error(f"{method} {path}: {exc.__class__.__name__}") from exc
    if response.status_code >= 400:
        try:
            message = response.json()["error"]["message"]
        except Exception:
            message = response.text[:200]
        raise Whisper360Error(f"{method} {path}: {response.status_code} {message}")
    return response.json()


def push_ticket(ticket):
    """Open the ticket on Whisper360 and record the link. Raises Whisper360Error."""
    data = _request("POST", "/v1/support/tickets", json=_payload(ticket))
    ticket.whisper_ticket_id = data["id"]
    ticket.whisper_sync_status = SupportTicket.WhisperSync.SYNCED
    ticket.whisper_sync_error = ""
    ticket.whisper_synced_at = timezone.now()
    ticket.save(
        update_fields=[
            "whisper_ticket_id",
            "whisper_sync_status",
            "whisper_sync_error",
            "whisper_synced_at",
            "updated_at",
        ]
    )
    return ticket


def push_ticket_safely(ticket_id):
    """Push one ticket, recording rather than raising any failure. For on_commit."""
    if not is_enabled():
        return
    ticket = (
        SupportTicket.objects.select_related("rider__user", "order")
        .filter(id=ticket_id, whisper_ticket_id__isnull=True)
        .first()
    )
    if ticket is None:
        return
    try:
        push_ticket(ticket)
    except Exception as exc:
        logger.warning("whisper360 push failed for %s: %s", ticket.reference, exc)
        SupportTicket.objects.filter(id=ticket.id).update(
            whisper_sync_status=SupportTicket.WhisperSync.FAILED,
            whisper_sync_error=str(exc)[:300],
        )


def refresh_ticket(ticket):
    """Copy Whisper360's status and the agent's latest reply onto the ticket. Raises Whisper360Error."""
    data = _request("GET", f"/v1/support/tickets/{ticket.whisper_ticket_id}")
    status = STATUS_FROM_WHISPER.get(data.get("status"), ticket.status)
    reply = data.get("latest_reply") or {}
    note = reply.get("body") or ticket.resolution_note
    if status in (SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED):
        resolved_at = parse_datetime(data["resolved_at"]) if data.get("resolved_at") else None
        resolved_at = resolved_at or ticket.resolved_at or timezone.now()
    else:
        # Reopened on the desk: the rider should not see it as resolved.
        resolved_at = None
    ticket.status = status
    ticket.resolution_note = note
    ticket.resolved_at = resolved_at
    ticket.whisper_synced_at = timezone.now()
    ticket.save(
        update_fields=[
            "status",
            "resolution_note",
            "resolved_at",
            "whisper_synced_at",
            "updated_at",
        ]
    )
    return ticket


def verify_signature(header, body, secret=None, now=None):
    """Whether `X-Whisper-Signature` ("t=<unix>,v1=<hex>") signs these exact bytes."""
    secret = secret if secret is not None else settings.WHISPER360_WEBHOOK_SECRET
    if not secret or not header:
        return False
    parts = dict(
        item.split("=", 1) for item in header.split(",") if "=" in item
    )
    try:
        stamp = int(parts.get("t", ""))
    except ValueError:
        return False
    now = int(now if now is not None else time.time())
    if abs(now - stamp) > SIGNATURE_TOLERANCE_SECONDS:
        return False
    expected = hmac.new(
        secret.encode(), f"{stamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, parts.get("v1", ""))
