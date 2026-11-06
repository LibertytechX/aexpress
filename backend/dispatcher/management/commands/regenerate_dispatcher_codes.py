import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import DispatcherProfile
from dispatcher.utils import generate_random_code

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Regenerates unique affiliation codes for dispatchers, replacing duplicate or "
        "legacy codes. By default, assigns fresh unique codes to all dispatchers."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-affiliates",
            action="store_true",
            default=False,
            help="Only assign codes to Hub Captains and Zone Leads; clear codes for Admin dispatchers.",
        )
        parser.add_argument(
            "--dispatcher-id",
            type=str,
            default=None,
            help="Specific dispatcher UUID to regenerate.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simulate the regeneration process without persisting changes to the database.",
        )

    def handle(self, *args, **options):
        only_affiliates = options["only_affiliates"]
        target_id = options["dispatcher_id"]
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.NOTICE(
                f"Starting dispatcher affiliation code regeneration (dry_run={dry_run}, only_affiliates={only_affiliates})..."
            )
        )

        qs = DispatcherProfile.objects.all().select_related("user").order_by("created_at")
        if target_id:
            qs = qs.filter(id=target_id)
            if not qs.exists():
                self.stderr.write(self.style.ERROR(f"No dispatcher found with ID {target_id}"))
                return

        total_dispatchers = qs.count()
        if total_dispatchers == 0:
            self.stdout.write(self.style.WARNING("No dispatchers found in database."))
            return

        self.stdout.write(f"Found {total_dispatchers} dispatcher(s) to process.\n")

        # Track existing codes to ensure absolute uniqueness across the database
        existing_codes = set(
            DispatcherProfile.objects.exclude(affiliation_code__isnull=True)
            .exclude(affiliation_code="")
            .values_list("affiliation_code", flat=True)
        )

        updated_count = 0
        cleared_count = 0

        with transaction.atomic():
            for profile in qs:
                user_label = (
                    profile.user.contact_name
                    or f"{profile.user.first_name} {profile.user.last_name}".strip()
                    or profile.user.phone
                    or str(profile.id)
                )
                role_label = profile.get_role_display()
                old_code = profile.affiliation_code or "—"

                # Check if this profile should have its code cleared
                if only_affiliates and profile.role not in [
                    DispatcherProfile.Role.ZONE_LEAD,
                    DispatcherProfile.Role.HUB_CAPTAIN,
                ]:
                    if profile.affiliation_code is not None:
                        if not dry_run:
                            profile.affiliation_code = None
                            profile.save(update_fields=["affiliation_code", "updated_at"])
                        cleared_count += 1
                        self.stdout.write(
                            f"  [CLEARED] {user_label} ({role_label}): Old={old_code} -> New=None (role not eligible)"
                        )
                    continue

                # Generate a guaranteed unique 6-character code
                while True:
                    candidate = generate_random_code(6).upper()
                    if candidate not in existing_codes:
                        existing_codes.add(candidate)
                        break

                if not dry_run:
                    profile.affiliation_code = candidate
                    profile.save(update_fields=["affiliation_code", "updated_at"])

                updated_count += 1
                self.stdout.write(
                    f"  [UPDATED] {user_label} ({role_label}): Old={old_code} -> New={candidate}"
                )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[DRY RUN] Rolled back changes. Would have updated {updated_count} dispatcher(s) and cleared {cleared_count}."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully regenerated affiliation codes for {updated_count} dispatcher(s)"
                        + (f" and cleared {cleared_count} non-affiliate dispatcher(s)." if cleared_count else ".")
                    )
                )
