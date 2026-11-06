"""
Rider support ticket API views.
All views require rider authentication.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from orders.permissions import IsRider
from .models import SupportTicket
from .serializers import SupportTicketSerializer


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

        serializer.save()
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
