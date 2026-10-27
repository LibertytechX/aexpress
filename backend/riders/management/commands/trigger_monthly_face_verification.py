from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from dispatcher.models import Rider
from riders.tasks import trigger_monthly_face_verification_task


class Command(BaseCommand):
    help = (
        "Triggers monthly face verification for independent riders whose last "
        "verification was over 30 days ago (or who have never verified and were "
        "created over 30 days ago). Updates rider authorization and publishes "
        "the 'facematch_required' Ably event."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days threshold for face verification (default: 30).",
        )
        parser.add_argument(
            "--rider-id",
            type=str,
            default=None,
            help="Target a specific rider by short rider_id or UUID.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List riders due for verification without modifying records or publishing events.",
        )
        parser.add_argument(
            "--async-task",
            action="store_true",
            help="Enqueue the task onto Celery instead of executing synchronously.",
        )

    def handle(self, *args, **options):
        days_threshold = options["days"]
        rider_id = options.get("rider_id")
        dry_run = options.get("dry_run", False)
        run_async = options.get("async_task", False)

        now = timezone.now()
        cutoff = now - timedelta(days=days_threshold)

        query = Rider.objects.filter(
            is_independent_rider=True,
            is_active=True,
            is_deleted=False,
            is_authorized=True,
            face_verification_required=False,
        )

        if rider_id:
            import uuid

            try:
                uuid.UUID(str(rider_id))
                is_uuid = True
            except (ValueError, AttributeError, TypeError):
                is_uuid = False

            if is_uuid:
                query = query.filter(Q(rider_id=rider_id) | Q(id=rider_id))
            else:
                query = query.filter(rider_id=rider_id)
        else:
            query = query.filter(
                Q(last_face_verified_at__isnull=False, last_face_verified_at__lte=cutoff)
                | Q(last_face_verified_at__isnull=True, created_at__lte=cutoff)
            )

        due_count = query.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Found {due_count} independent rider(s) due for face verification (threshold: {days_threshold} days)."
                )
            )
            for rider in query:
                self.stdout.write(
                    f" - Rider: {rider.rider_id} (ID: {rider.id}), "
                    f"Last Verified: {rider.last_face_verified_at}, "
                    f"Created At: {rider.created_at}"
                )
            return

        if run_async:
            task = trigger_monthly_face_verification_task.delay(
                days_threshold=days_threshold,
                rider_id=rider_id,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dispatched Celery task {task.id} to trigger face verification for {due_count} rider(s)."
                )
            )
            return

        result = trigger_monthly_face_verification_task(
            days_threshold=days_threshold,
            rider_id=rider_id,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully triggered face verification for {result['processed_count']} rider(s): {result['due_riders']}"
            )
        )
