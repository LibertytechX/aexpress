import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class RiderAuth(models.Model):
    """
    Auth credentials for rider app login.
    Linked to dispatcher.Rider via OneToOne.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.OneToOneField(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="auth"
    )
    password_hash = models.CharField(max_length=255)
    pin = models.CharField(max_length=255, blank=True, default="")
    biometric_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Device-specific biometric auth token",
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # OTP for phone verification / password reset
    otp_code = models.CharField(max_length=6, blank=True, default="")
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_auth"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_failed_attempt(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=["failed_attempts", "locked_until"])

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_attempts", "locked_until"])


class RiderSession(models.Model):
    """
    JWT refresh token tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="sessions"
    )
    refresh_token = models.CharField(max_length=500, unique=True, db_index=True)
    device_id = models.CharField(max_length=255, blank=True, default="")
    device_name = models.CharField(max_length=255, blank=True, default="")
    device_os = models.CharField(max_length=50, blank=True, default="")
    fcm_token = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "rider_sessions"
        ordering = ["-last_used_at"]


class RiderCodRecord(models.Model):
    """
    Tracks Cash On Delivery collections and remissions per rider.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Remission"
        REMITTED = "remitted", "Remitted"
        VERIFIED = "verified", "Verified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="cod_records"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="cod_records"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    remitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_cod_records"
        ordering = ["-created_at"]


class RiderEarning(models.Model):
    """
    Per-trip earnings breakdown.
    """

    from decimal import Decimal

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="earnings"
    )
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="rider_earning"
    )
    base_fare = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    distance_fare = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    surge_bonus = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("20.00")
    )
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    net_earning = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cod_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_earnings"
        ordering = ["-created_at"]


class RiderDocument(models.Model):
    """
    KYC documents for riders.
    """

    class DocType(models.TextChoices):
        DRIVERS_LICENSE = "drivers_license", "Driver's License"
        VEHICLE_INSURANCE = "vehicle_insurance", "Vehicle Insurance"
        VEHICLE_REGISTRATION = "vehicle_registration", "Vehicle Registration"
        NATIONAL_ID = "national_id", "National ID"
        PROFILE_PHOTO = "profile_photo", "Profile Photo"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    file_url = models.URLField(max_length=500)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    expires_at = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_documents"
        ordering = ["-created_at"]


class OrderOffer(models.Model):
    """
    An order offered to a rider.
    """

    from decimal import Decimal

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="rider_offers"
    )
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="order_offers",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    estimated_earnings = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_offers"
        ordering = ["-created_at"]


class RiderDevice(models.Model):
    """
    Rider device tracking and permissions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="devices"
    )
    device_id = models.CharField(max_length=255, unique=True, db_index=True)
    fcm_token = models.CharField(max_length=500, blank=True, default="")
    platform = models.CharField(max_length=50, blank=True, default="")
    model_name = models.CharField(max_length=255, blank=True, default="")
    os_version = models.CharField(max_length=50, blank=True, default="")
    app_version = models.CharField(max_length=50, blank=True, default="")

    # Permissions tracking
    location_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    camera_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    notification_permission = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )
    battery_optimization = models.CharField(
        max_length=50, blank=True, default="undetermined"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_devices"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Device {self.device_id} ({self.rider.rider_id})"


class AreaDemand(models.Model):
    """
    Real-time demand levels per area. Updated by Celery task.
    Shown on the Off-Duty screen.
    """

    class Level(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    area_name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.LOW)
    pending_orders = models.IntegerField(default=0)
    active_riders = models.IntegerField(default=0)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "area_demand"
        ordering = ["area_name"]


class RiderNotification(models.Model):
    """
    Persisted notifications sent to riders.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "rider_notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.rider.rider_id}: {self.title}"


class RiderLocation(models.Model):
    """
    Live GPS location for a rider.
    One record per rider — upserted on every ping from the mobile app.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.OneToOneField(
        "dispatcher.Rider", on_delete=models.CASCADE, related_name="location"
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    accuracy = models.FloatField(
        null=True, blank=True, help_text="GPS accuracy in metres"
    )
    heading = models.FloatField(
        null=True, blank=True, help_text="Bearing in degrees (0-360)"
    )
    speed = models.FloatField(null=True, blank=True, help_text="Speed in m/s")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_locations"

    def __str__(self):
        return (
            f"Location for {self.rider.rider_id}: ({self.latitude}, {self.longitude})"
        )


# ---------------------------------------------------------------------------
# Gamification Models
# ---------------------------------------------------------------------------


class RideToOwnConfig(models.Model):
    """
    System-wide configuration for the Ride to Own program.
    Only one active record is used at a time.
    """

    total_orders_target = models.IntegerField(
        default=7800,
        help_text="Total orders a rider must complete to own their assigned bike.",
    )
    program_duration_months = models.IntegerField(
        default=12,
        help_text="Duration of the program in months.",
    )
    description = models.TextField(
        blank=True,
        default="Complete the target number of orders within the program period to own your bike.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ride_to_own_config"

    def __str__(self):
        return f"RideToOwnConfig: {self.total_orders_target} orders / {self.program_duration_months} months"

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()


class RideToOwnEnrollment(models.Model):
    """
    Per-rider enrollment in the Ride to Own program.
    Created when admin assigns a bike to a rider.
    Progress (orders_done, pct_complete, pace) is computed at query time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.OneToOneField(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="ride_to_own",
    )
    vehicle_asset = models.ForeignKey(
        "dispatcher.VehicleAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ride_to_own_enrollments",
        help_text="The pre-assigned bike this rider is earning.",
    )
    start_date = models.DateField()
    end_date = models.DateField(help_text="start_date + program_duration_months")
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ride_to_own_enrollments"

    def __str__(self):
        return f"RideToOwn: {self.rider.rider_id}"

    def get_orders_done(self):
        from orders.models import Order
        return Order.objects.filter(
            rider=self.rider,
            status="Done",
            completed_at__date__gte=self.start_date,
            completed_at__date__lte=self.end_date,
        ).count()

    def get_progress(self):
        """Returns a dict with all computed progress fields."""
        from orders.models import Order
        from decimal import Decimal
        import math

        config = RideToOwnConfig.get_active()
        total_needed = config.total_orders_target if config else 7800

        orders_done = self.get_orders_done()
        orders_to_go = max(total_needed - orders_done, 0)
        pct_complete = round((orders_done / total_needed) * 100, 1) if total_needed else 0

        today = timezone.now().date()
        days_elapsed = max((today - self.start_date).days, 1)
        days_total = max((self.end_date - self.start_date).days, 1)
        days_remaining = max((self.end_date - today).days, 0)
        months_remaining = math.ceil(days_remaining / 30)

        avg_orders_per_day = round(orders_done / days_elapsed, 1)
        orders_per_day_needed = (
            round(orders_to_go / days_remaining, 1) if days_remaining > 0 else 0
        )

        # Monthly timeline (which months are complete)
        monthly_timeline = []
        for i in range(config.program_duration_months if config else 12):
            from datetime import date
            from dateutil.relativedelta import relativedelta
            month_start = self.start_date + relativedelta(months=i)
            month_end = month_start + relativedelta(months=1)
            is_complete = today >= month_end
            is_current = month_start <= today < month_end
            monthly_timeline.append({
                "month_number": i + 1,
                "month_label": month_start.strftime("%b"),
                "is_complete": is_complete,
                "is_current": is_current,
            })

        return {
            "orders_done": orders_done,
            "orders_to_go": orders_to_go,
            "total_needed": total_needed,
            "pct_complete": pct_complete,
            "avg_orders_per_day": avg_orders_per_day,
            "orders_per_day_needed": orders_per_day_needed,
            "months_remaining": months_remaining,
            "monthly_timeline": monthly_timeline,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_completed": self.completed_at is not None,
        }


class RiderMonthlyTarget(models.Model):
    """
    Monthly earnings target for a rider.
    Can be admin-set (is_auto=False) or auto-calculated (is_auto=True).
    Progress is computed at query time from RiderEarning records.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="monthly_targets",
    )
    month = models.DateField(
        help_text="First day of the target month, e.g. 2026-03-01"
    )
    target_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monthly earnings target in Naira.",
    )
    target_orders_per_day = models.IntegerField(
        default=25,
        help_text="Daily order target used for pace calculations.",
    )
    is_auto = models.BooleanField(
        default=True,
        help_text="True = auto-calculated, False = admin-set.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_monthly_targets"
        unique_together = ("rider", "month")
        ordering = ["-month"]

    def __str__(self):
        return f"MonthlyTarget: {self.rider.rider_id} / {self.month.strftime('%b %Y')} — ₦{self.target_earnings}"

    def get_progress(self):
        """Returns full progress data for the monthly target view."""
        from orders.models import Order
        from decimal import Decimal
        import calendar

        today = timezone.now().date()
        month_start = self.month
        # Last day of this month
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_end = month_start.replace(day=last_day)

        # Total earnings this month
        earned = RiderEarning.objects.filter(
            rider=self.rider,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
        ).aggregate(total=models.Sum("net_earning"))["total"] or Decimal("0.00")

        remaining = max(self.target_earnings - earned, Decimal("0.00"))
        pct = round(float(earned / self.target_earnings) * 100, 1) if self.target_earnings else 0

        # Daily orders chart — current week
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())  # Monday
        daily_chart = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            count = Order.objects.filter(
                rider=self.rider,
                status="Done",
                completed_at__date=day,
            ).count()
            if count >= self.target_orders_per_day:
                color = "green"
            elif count >= 20:
                color = "amber"
            else:
                color = "orange"
            daily_chart.append({
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "orders": count,
                "color": color,
                "is_future": day > today,
            })

        # This week summary
        week_orders_done = Order.objects.filter(
            rider=self.rider,
            status="Done",
            completed_at__date__gte=week_start,
            completed_at__date__lte=today,
        ).count()
        days_at_target_this_week = sum(
            1 for d in daily_chart
            if not d["is_future"] and d["orders"] >= self.target_orders_per_day
        )
        work_days_left = sum(1 for d in daily_chart if d["is_future"] and d["day"] not in ("Sat", "Sun"))

        # Days elapsed in month
        days_elapsed = max((today - month_start).days + 1, 1)
        days_remaining_month = max((month_end - today).days, 0)
        avg_per_day = round(float(earned) / days_elapsed, 0)

        # Milestones
        milestone_amounts = [50000, 100000, 150000, 200000, float(self.target_earnings)]
        milestones = []
        for amt in milestone_amounts:
            milestones.append({
                "amount": amt,
                "is_reached": float(earned) >= amt,
                "is_next": float(earned) < amt and all(float(earned) >= m for m in milestone_amounts if m < amt),
            })

        # Behind / on track
        expected_by_now = float(self.target_earnings) * (days_elapsed / max((month_end - month_start).days + 1, 1))
        is_behind = float(earned) < expected_by_now * 0.9  # 10% tolerance

        return {
            "month": month_start.strftime("%B %Y"),
            "target_earnings": self.target_earnings,
            "earned": earned,
            "remaining": remaining,
            "pct_complete": pct,
            "is_behind": is_behind,
            "days_remaining": days_remaining_month,
            "avg_earnings_per_day": avg_per_day,
            "daily_chart": daily_chart,
            "milestones": milestones,
            "week_summary": {
                "orders_done": week_orders_done,
                "target_orders": self.target_orders_per_day * 5,
                "orders_remaining": max(self.target_orders_per_day * 5 - week_orders_done, 0),
                "work_days_left": work_days_left,
                "days_at_target": days_at_target_this_week,
                "pct": round(week_orders_done / (self.target_orders_per_day * 5) * 100, 1),
            },
        }


class RiderStreak(models.Model):
    """
    Tracks consecutive calendar days where a rider completed >= 25 orders.
    One record per rider, updated by the order-completion signal handler.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.OneToOneField(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="streak",
    )
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_streak_date = models.DateField(
        null=True,
        blank=True,
        help_text="The last calendar day that counted toward the streak.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_streaks"

    def __str__(self):
        return f"Streak: {self.rider.rider_id} — {self.current_streak} days"


class Challenge(models.Model):
    """
    Admin-managed challenge definition.
    """

    class RewardType(models.TextChoices):
        CASH = "cash", "Cash"
        PERK = "perk", "Perk"

    class Metric(models.TextChoices):
        ORDERS_COUNT_DAY = "orders_count_day", "Orders per Day"
        ORDERS_COUNT_WEEK = "orders_count_week", "Orders per Week"
        STREAK_DAYS = "streak_days", "Streak Days"
        NO_CANCELLATIONS = "no_cancellations", "No Cancellations"
        REFERRALS_COUNT = "referrals_count", "Referrals Count"

    class Period(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        ONGOING = "ongoing", "Ongoing"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon_emoji = models.CharField(max_length=10, default="🏆")
    reward_type = models.CharField(
        max_length=10, choices=RewardType.choices, default=RewardType.CASH
    )
    reward_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cash reward amount. Leave blank for perk rewards.",
    )
    reward_perk = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="e.g. 'priority_dispatch'",
    )
    metric = models.CharField(max_length=30, choices=Metric.choices)
    metric_target = models.IntegerField(help_text="Target value to complete the challenge.")
    metric_condition = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra conditions, e.g. {'before_hour': 9, 'min_per_day': 25}",
    )
    period = models.CharField(
        max_length=10, choices=Period.choices, default=Period.MONTHLY
    )
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "challenges"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.icon_emoji} {self.name}"


class RiderChallengeProgress(models.Model):
    """
    Per-rider progress on a given challenge.
    Created automatically when a challenge becomes active.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="challenge_progress",
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="rider_progress",
    )
    current_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    reward_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rider_challenge_progress"
        unique_together = ("rider", "challenge")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rider.rider_id} — {self.challenge.name}: {self.current_value}/{self.challenge.metric_target}"

    @property
    def pct_complete(self):
        if self.challenge.metric_target == 0:
            return 100
        return round((self.current_value / self.challenge.metric_target) * 100, 1)


class LeaderboardEntry(models.Model):
    """
    Cached leaderboard snapshot. Rebuilt nightly by the rebuild_leaderboard management command.
    """

    class PeriodType(models.TextChoices):
        THIS_WEEK = "this_week", "This Week"
        THIS_MONTH = "this_month", "This Month"
        ALL_TIME = "all_time", "All Time"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rider = models.ForeignKey(
        "dispatcher.Rider",
        on_delete=models.CASCADE,
        related_name="leaderboard_entries",
    )
    period_type = models.CharField(max_length=15, choices=PeriodType.choices, db_index=True)
    period_key = models.CharField(
        max_length=20,
        db_index=True,
        help_text="e.g. '2026-W10', '2026-03', 'all_time'",
    )
    rank = models.IntegerField()
    trips_count = models.IntegerField(default=0)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    zone_name = models.CharField(max_length=100, blank=True, default="")
    rebuilt_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leaderboard_entries"
        unique_together = ("rider", "period_type", "period_key")
        ordering = ["rank"]

    def __str__(self):
        return f"#{self.rank} {self.rider.rider_id} — {self.period_type} ({self.period_key})"
