import uuid
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from dispatcher.models import Rider
from authentication.models import User
from orders.models import Order, Vehicle
from riders.models import RiderEarning, RiderCodRecord


def verify_earnings():
    print("--- Starting Manual Verification ---")

    # 1. Create Clean Test Data
    phone = f"080{str(uuid.uuid4().int)[:8]}"
    user = User.objects.create_user(
        phone=phone,
        email=f"{phone}@example.com",
        password="password123",
        first_name="Manual",
        last_name="Tester",
    )
    rider = Rider.objects.create(
        user=user, rider_id=f"R{str(uuid.uuid4().int)[:5]}", status="online"
    )

    vehicle, _ = Vehicle.objects.get_or_create(
        name="Bike",
        defaults={
            "max_weight_kg": 10,
            "base_fare": 500.00,
            "rate_per_km": 100.00,
            "base_price": 500.00,
        },
    )

    print(f"Created Rider: {rider.rider_id}")

    # 2. Today's Earning
    now = timezone.now()
    order1 = Order.objects.create(
        user=user,
        rider=rider,
        vehicle=vehicle,
        pickup_address="Cleanup St",
        total_amount=Decimal("2000.00"),
        status="Done",
        completed_at=now,
    )
    RiderEarning.objects.create(
        rider=rider, order=order1, net_earning=Decimal("1600.00"), created_at=now
    )
    RiderCodRecord.objects.create(
        rider=rider,
        order=order1,
        amount=Decimal("2000.00"),
        status=RiderCodRecord.Status.VERIFIED,
        created_at=now,
    )

    # 3. Yesterday's Earning (should show in week, but not today)
    yesterday = now - timedelta(days=1)
    order2 = Order.objects.create(
        user=user,
        rider=rider,
        vehicle=vehicle,
        pickup_address="History Ave",
        total_amount=Decimal("1000.00"),
        status="Done",
        completed_at=yesterday,
    )
    RiderEarning.objects.create(
        rider=rider, order=order2, net_earning=Decimal("800.00"), created_at=yesterday
    )

    print("Data created. Verifying logic...")

    # Mocking the View logic for verification since we are in shell-like script
    def get_stats(rider, period):
        now = timezone.now()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=30)

        total_earnings = (
            RiderEarning.objects.filter(
                rider=rider, created_at__gte=start_date
            ).aggregate(Sum("net_earning"))["net_earning__sum"]
            or 0
        )

        trips = Order.objects.filter(
            rider=rider, status="Done", completed_at__gte=start_date
        ).count()

        cod = (
            RiderCodRecord.objects.filter(
                rider=rider, status="verified", created_at__gte=start_date
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )

        return total_earnings, trips, cod

    today_vals = get_stats(rider, "today")
    week_vals = get_stats(rider, "week")

    print(
        f"Today Stats -> Earnings: {today_vals[0]}, Trips: {today_vals[1]}, COD: {today_vals[2]}"
    )
    print(
        f"Week Stats  -> Earnings: {week_vals[0]}, Trips: {week_vals[1]}, COD: {week_vals[2]}"
    )

    assert today_vals[1] == 1, "Today should have 1 trip"
    assert week_vals[1] == 2, "Week should have 2 trips"
    assert today_vals[0] == Decimal("1600.00"), "Today earnings mismatch"
    assert today_vals[2] == Decimal("2000.00"), "Today COD mismatch"

    print("--- Verification Successful! ---")


if __name__ == "__main__":
    verify_earnings()
