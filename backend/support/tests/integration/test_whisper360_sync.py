"""
Rider tickets reach Whisper360's Support desk, and the desk's answer comes back.

Whisper360's HTTP API is faked here; the contract it stands in for is
POST/GET /v1/support/tickets in Whisper360 (docs/api/support-tickets-from-your-app.md).
"""

import hashlib
import hmac
import json
import time
import uuid

import httpx
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import Rider
from support import whisper360
from support.models import SupportTicket

WHISPER_ID = str(uuid.uuid4())
SECRET = "whsec_test"


@pytest.fixture
def enabled(settings):
    settings.WHISPER360_API_URL = "https://api.whisper360.test"
    settings.WHISPER360_API_KEY = "w360_live_test"
    settings.WHISPER360_WEBHOOK_SECRET = SECRET
    settings.WHISPER360_SUPPORT_QUEUE_ID = ""
    return settings


@pytest.fixture
def rider(db):
    user = User.objects.create_user(
        phone="08012345678", password="password123", first_name="Ada", last_name="Obi"
    )
    return Rider.objects.create(user=user, rider_id="RID123", status="online")


class FakeWhisper:
    """Records requests and answers like Whisper360's /v1/support/tickets."""

    def __init__(self, monkeypatch):
        self.calls = []
        self.ticket = {
            "object": "support_ticket",
            "id": WHISPER_ID,
            "status": "open",
            "resolved_at": None,
            "latest_reply": None,
        }
        self.fail_with = None
        monkeypatch.setattr(whisper360.httpx, "request", self.request)

    def request(self, method, url, headers=None, timeout=None, json=None):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json})
        if self.fail_with is not None:
            raise self.fail_with
        status = 201 if method == "POST" else 200
        return httpx.Response(status, json=self.ticket, request=httpx.Request(method, url))


@pytest.fixture
def fake(monkeypatch):
    return FakeWhisper(monkeypatch)


def _submit(rider, django_capture_on_commit_callbacks, **extra):
    client = APIClient()
    client.force_authenticate(user=rider.user)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("support:ticket-create"),
            {
                "category": "order",
                "subject": "Customer not at drop-off",
                "message": "Waited 20 minutes.",
                **extra,
            },
            format="json",
        )
    assert response.status_code == 201, response.content
    return SupportTicket.objects.get(reference=response.data["data"]["reference"])


def _signed(body, secret=SECRET, stamp=None):
    stamp = stamp or int(time.time())
    digest = hmac.new(secret.encode(), f"{stamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={stamp},v1={digest}"


def _deliver(event, signature=None):
    body = json.dumps(event).encode()
    return APIClient().post(
        reverse("support:whisper360-webhook"),
        data=body,
        content_type="application/json",
        HTTP_X_WHISPER_SIGNATURE=signature or _signed(body),
    )


@pytest.mark.django_db
class TestPush:
    def test_a_submitted_ticket_is_pushed_once_committed(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        ticket = _submit(rider, django_capture_on_commit_callbacks)

        ticket.refresh_from_db()
        assert str(ticket.whisper_ticket_id) == WHISPER_ID
        assert ticket.whisper_sync_status == SupportTicket.WhisperSync.SYNCED
        sent = fake.calls[0]
        assert sent["method"] == "POST"
        assert sent["url"] == "https://api.whisper360.test/v1/support/tickets"
        assert sent["headers"]["Authorization"] == "Bearer w360_live_test"
        body = sent["json"]
        assert body["external_id"] == str(ticket.id)
        assert body["user_id"] == str(rider.id)
        assert body["priority"] == "normal"  # our "medium"
        assert body["details"]["Reference"] == ticket.reference
        assert body["details"]["Category"] == "Order / Delivery"

    def test_whisper360_down_never_fails_the_rider(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        fake.fail_with = httpx.ConnectError("refused")
        ticket = _submit(rider, django_capture_on_commit_callbacks)

        ticket.refresh_from_db()
        assert ticket.whisper_ticket_id is None
        assert ticket.whisper_sync_status == SupportTicket.WhisperSync.FAILED
        assert "ConnectError" in ticket.whisper_sync_error

        # The sync command retries it.
        fake.fail_with = None
        call_command("sync_whisper360_tickets", "--no-refresh")
        ticket.refresh_from_db()
        assert ticket.whisper_sync_status == SupportTicket.WhisperSync.SYNCED

    def test_nothing_is_sent_while_the_integration_is_off(
        self, fake, rider, django_capture_on_commit_callbacks, settings
    ):
        settings.WHISPER360_API_URL = ""
        ticket = _submit(rider, django_capture_on_commit_callbacks)
        assert fake.calls == []
        ticket.refresh_from_db()
        assert ticket.whisper_sync_status == SupportTicket.WhisperSync.PENDING


@pytest.mark.django_db
class TestWebhook:
    def _synced(self, enabled, fake, rider, capture):
        ticket = _submit(rider, capture)
        fake.calls.clear()
        return ticket

    def test_a_reply_and_resolution_reach_the_rider(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        ticket = self._synced(enabled, fake, rider, django_capture_on_commit_callbacks)
        fake.ticket.update(
            status="resolved",
            resolved_at="2026-11-09T10:30:00+00:00",
            latest_reply={
                "id": str(uuid.uuid4()),
                "body": "We have paid your waiting fee.",
                "occurred_at": "2026-11-09T10:29:00+00:00",
            },
        )

        response = _deliver(
            {"event_name": "conversation.status_changed", "data": {"conversation_id": WHISPER_ID}}
        )

        assert response.status_code == 200
        assert fake.calls[0]["method"] == "GET"
        assert fake.calls[0]["url"].endswith(f"/v1/support/tickets/{WHISPER_ID}")
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.RESOLVED
        assert ticket.resolution_note == "We have paid your waiting fee."
        assert ticket.resolved_at is not None

        # The rider app reads it through the existing endpoint.
        client = APIClient()
        client.force_authenticate(user=rider.user)
        data = client.get(
            reverse("support:ticket-detail", args=[ticket.reference])
        ).data["data"]
        assert data["status"] == "resolved"
        assert data["resolution_note"] == "We have paid your waiting fee."

    def test_a_reopened_ticket_is_no_longer_resolved(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        ticket = self._synced(enabled, fake, rider, django_capture_on_commit_callbacks)
        SupportTicket.objects.filter(id=ticket.id).update(status="resolved")
        fake.ticket.update(status="pending")

        _deliver({"event_name": "message.sent", "data": {"conversation_id": WHISPER_ID}})

        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.IN_PROGRESS
        assert ticket.resolved_at is None

    def test_a_forged_or_stale_delivery_is_refused(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        self._synced(enabled, fake, rider, django_capture_on_commit_callbacks)
        event = {"event_name": "message.sent", "data": {"conversation_id": WHISPER_ID}}
        body = json.dumps(event).encode()

        assert _deliver(event, signature=_signed(body, secret="wrong")).status_code == 401
        stale = _signed(body, stamp=int(time.time()) - 3600)
        assert _deliver(event, signature=stale).status_code == 401
        assert fake.calls == []

    def test_other_conversations_and_events_are_ignored(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        self._synced(enabled, fake, rider, django_capture_on_commit_callbacks)
        unknown = _deliver(
            {"event_name": "message.sent", "data": {"conversation_id": str(uuid.uuid4())}}
        )
        other_event = _deliver(
            {"event_name": "contact.created", "data": {"conversation_id": WHISPER_ID}}
        )
        assert unknown.json() == {"ignored": True}
        assert other_event.json() == {"ignored": True}
        assert fake.calls == []

    def test_a_failed_read_back_asks_whisper360_to_retry(
        self, enabled, fake, rider, django_capture_on_commit_callbacks
    ):
        self._synced(enabled, fake, rider, django_capture_on_commit_callbacks)
        fake.fail_with = httpx.ReadTimeout("slow")
        response = _deliver(
            {"event_name": "message.sent", "data": {"conversation_id": WHISPER_ID}}
        )
        assert response.status_code == 502


@pytest.mark.django_db
def test_synced_tickets_are_read_only_in_admin(enabled, fake, rider, django_capture_on_commit_callbacks):
    from django.contrib.admin.sites import site

    ticket = _submit(rider, django_capture_on_commit_callbacks)
    ticket.refresh_from_db()
    admin = site._registry[SupportTicket]
    fields = admin.get_readonly_fields(request=None, obj=ticket)
    assert {"status", "priority", "resolution_note"} <= set(fields)
