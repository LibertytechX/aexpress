import pytest
from decimal import Decimal
from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import User
from dispatcher.models import Rider
from orders.models import Order, Vehicle
from support.models import SupportTicket
from support.views import SupportTicketCreateView


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rider_user(db):
    user = User.objects.create_user(
        phone="08012345678",
        password="password123",
        first_name="Test",
        last_name="Rider",
    )
    rider = Rider.objects.create(user=user, rider_id="RID123", status="online")
    return user, rider


@pytest.fixture
def other_rider_user(db):
    user = User.objects.create_user(
        phone="08087654321",
        password="password123",
        first_name="Other",
        last_name="Rider",
    )
    rider = Rider.objects.create(user=user, rider_id="RID456", status="online")
    return user, rider


@pytest.fixture
def vehicle(db):
    return Vehicle.objects.create(
        name="Bike",
        max_weight_kg=10,
        base_fare=500.00,
        rate_per_km=100.00,
        base_price=500.00,
    )


def make_order(user, rider, vehicle):
    return Order.objects.create(
        user=user,
        rider=rider,
        vehicle=vehicle,
        pickup_address="A",
        total_amount=Decimal("1500.00"),
    )


@pytest.mark.django_db
class TestSupportTickets:
    def test_url_resolves_to_support_app(self):
        # api/riders/ is mounted before api/riders/support/ — make sure riders.urls doesn't swallow it
        assert resolve("/api/riders/support/").func.view_class is SupportTicketCreateView

    def test_rider_can_create_ticket(self, api_client, rider_user):
        user, rider = rider_user
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("support:ticket-create"),
            {
                "category": "payment",
                "subject": "Payment not received",
                "message": "I completed an order but wasn't paid.",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["status"] == "open"
        assert response.data["data"]["reference"].startswith("TCK-")
        ticket = SupportTicket.objects.get()
        assert ticket.rider == rider

    def test_create_ticket_linked_to_own_order(
        self, api_client, rider_user, vehicle
    ):
        user, rider = rider_user
        order = make_order(user, rider, vehicle)
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("support:ticket-create"),
            {
                "category": "order",
                "subject": "Wrong address",
                "message": "Drop-off address was wrong.",
                "order_number": order.order_number,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["order"] == order.order_number

    def test_cannot_link_another_riders_order(
        self, api_client, rider_user, other_rider_user, vehicle
    ):
        user, _ = rider_user
        other_user, other_rider = other_rider_user
        order = make_order(other_user, other_rider, vehicle)
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("support:ticket-create"),
            {
                "subject": "Test",
                "message": "Test",
                "order_number": order.order_number,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "order_number" in response.data["errors"]
        assert SupportTicket.objects.count() == 0

    def test_missing_fields_rejected(self, api_client, rider_user):
        user, _ = rider_user
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("support:ticket-create"), {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "subject" in response.data["errors"]
        assert "message" in response.data["errors"]

    def test_rider_only_sees_own_tickets(
        self, api_client, rider_user, other_rider_user
    ):
        user, rider = rider_user
        _, other_rider = other_rider_user
        SupportTicket.objects.create(rider=rider, subject="Mine", message="x")
        SupportTicket.objects.create(rider=other_rider, subject="Theirs", message="x")
        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("support:ticket-list"))

        assert response.status_code == status.HTTP_200_OK
        subjects = [t["subject"] for t in response.data["data"]]
        assert subjects == ["Mine"]

    def test_list_filters_by_status(self, api_client, rider_user):
        user, rider = rider_user
        SupportTicket.objects.create(rider=rider, subject="Open", message="x")
        SupportTicket.objects.create(
            rider=rider,
            subject="Done",
            message="x",
            status=SupportTicket.Status.RESOLVED,
        )
        api_client.force_authenticate(user=user)

        response = api_client.get(
            reverse("support:ticket-list"), {"status": "resolved"}
        )

        assert [t["subject"] for t in response.data["data"]] == ["Done"]

    def test_ticket_detail(self, api_client, rider_user, other_rider_user):
        user, rider = rider_user
        _, other_rider = other_rider_user
        mine = SupportTicket.objects.create(rider=rider, subject="Mine", message="x")
        theirs = SupportTicket.objects.create(
            rider=other_rider, subject="Theirs", message="x"
        )
        api_client.force_authenticate(user=user)

        ok = api_client.get(reverse("support:ticket-detail", args=[mine.reference]))
        assert ok.status_code == status.HTTP_200_OK
        assert ok.data["data"]["subject"] == "Mine"

        hidden = api_client.get(
            reverse("support:ticket-detail", args=[theirs.reference])
        )
        assert hidden.status_code == status.HTTP_404_NOT_FOUND

    def test_non_rider_is_forbidden(self, api_client, db):
        user = User.objects.create_user(phone="08000000000", password="password123")
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("support:ticket-create"),
            {"subject": "x", "message": "x"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_is_rejected(self, api_client, db):
        response = api_client.get(reverse("support:ticket-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
