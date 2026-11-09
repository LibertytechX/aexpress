"""
Rider support ticket API views.
All rider views require rider authentication. The Whisper360 webhook is
authenticated by its signature instead.
"""

import json
import logging

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from orders.permissions import IsRider
from . import whisper360
from .models import SupportTicket
from .serializers import SupportTicketSerializer

logger = logging.getLogger(__name__)

# The Whisper360 events that can change what the rider sees.
WHISPER360_TICKET_EVENTS = {"message.sent", "conversation.status_changed"}


def get_rider(user):
    """Helper to get rider profile from user."""
    return getattr(user, "rider_profile", None)


def rider_not_found():
    return Response(
        {"success": False, "message": "Rider profile not found."},
        status=status.HTTP_404_NOT_FOUND,
    )


class SupportTicketCreateView(APIView):
    """
    POST /api/riders/support/
    Lodge a new complaint / support ticket.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request):
        rider = get_rider(request.user)
        if not rider:
            return rider_not_found()

        serializer = SupportTicketSerializer(
            data=request.data, context={"rider": rider}
        )
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket = serializer.save()
        # After commit, so Whisper360 is never told about a ticket that rolled back.
        # A failed push is recorded on the ticket, never returned to the rider.
        transaction.on_commit(lambda: whisper360.push_ticket_safely(ticket.id))
        return Response(
            {
                "success": True,
                "message": "Ticket submitted successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class SupportTicketListView(APIView):
    """
    GET /api/riders/support/tickets/
    List the rider's own tickets. Optional ?status= filter.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return rider_not_found()

        tickets = SupportTicket.objects.filter(rider=rider).select_related("order")
        status_filter = request.query_params.get("status")
        if status_filter:
            tickets = tickets.filter(status=status_filter)

        serializer = SupportTicketSerializer(tickets, many=True)
        return Response({"success": True, "data": serializer.data})


class SupportTicketDetailView(APIView):
    """
    GET /api/riders/support/tickets/<reference>/
    Retrieve one of the rider's own tickets.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request, reference):
        rider = get_rider(request.user)
        if not rider:
            return rider_not_found()

        ticket = (
            SupportTicket.objects.filter(rider=rider, reference=reference)
            .select_related("order")
            .first()
        )
        if not ticket:
            return Response(
                {"success": False, "message": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"success": True, "data": SupportTicketSerializer(ticket).data}
        )


@csrf_exempt
@require_POST
def whisper360_webhook(request):
    """
    POST /api/riders/support/whisper360/webhook/
    Whisper360 tells us a ticket changed; we read it back and update our copy.
    Events carry ids only, so the reply text always comes from the read.
    """
    if not whisper360.verify_signature(
        request.headers.get("X-Whisper-Signature", ""), request.body
    ):
        return JsonResponse({"detail": "Invalid signature."}, status=401)
    try:
        event = json.loads(request.body)
    except ValueError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    if event.get("event_name") not in WHISPER360_TICKET_EVENTS:
        return JsonResponse({"ignored": True})
    conversation_id = (event.get("data") or {}).get("conversation_id")
    ticket = (
        SupportTicket.objects.filter(whisper_ticket_id=conversation_id).first()
        if conversation_id
        else None
    )
    if ticket is None:
        # Some other conversation in the workspace, not a rider ticket.
        return JsonResponse({"ignored": True})
    try:
        whisper360.refresh_ticket(ticket)
    except Exception as exc:
        logger.warning("whisper360 refresh failed for %s: %s", ticket.reference, exc)
        # Non-2xx makes Whisper360 retry the delivery.
        return JsonResponse({"detail": "Could not read the ticket back."}, status=502)
    return JsonResponse({"updated": ticket.reference})
