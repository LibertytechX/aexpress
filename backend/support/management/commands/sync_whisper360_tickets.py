"""
Push rider tickets Whisper360 has not got yet, and re-read the open ones.

    python manage.py sync_whisper360_tickets            # push pending/failed, refresh open
    python manage.py sync_whisper360_tickets --dry-run  # say what it would do

Safe to run as often as you like: Whisper360 opens one ticket per our ticket id,
so a push that already landed returns the same ticket. Run it once after
enabling the integration to backfill existing tickets, then on a schedule as a
safety net for missed webhooks.
"""

from django.core.management.base import BaseCommand, CommandError

from support import whisper360
from support.models import SupportTicket


class Command(BaseCommand):
    help = "Push unsynced rider tickets to Whisper360 and refresh open ones."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--no-refresh",
            action="store_true",
            help="Only push; do not re-read open tickets.",
        )

    def handle(self, *args, **options):
        if not whisper360.is_enabled():
            raise CommandError("Set WHISPER360_API_URL and WHISPER360_API_KEY first.")
        dry_run = options["dry_run"]

        to_push = SupportTicket.objects.filter(
            whisper_ticket_id__isnull=True
        ).select_related("rider__user", "order").order_by("created_at")
        pushed = failed = 0
        for ticket in to_push:
            if dry_run:
                self.stdout.write(f"would push {ticket.reference}")
                continue
            try:
                whisper360.push_ticket(ticket)
                pushed += 1
            except whisper360.Whisper360Error as exc:
                failed += 1
                SupportTicket.objects.filter(id=ticket.id).update(
                    whisper_sync_status=SupportTicket.WhisperSync.FAILED,
                    whisper_sync_error=str(exc)[:300],
                )
                self.stderr.write(f"{ticket.reference}: {exc}")

        refreshed = refresh_failed = 0
        if not options["no_refresh"]:
            open_tickets = SupportTicket.objects.filter(
                whisper_ticket_id__isnull=False
            ).exclude(status=SupportTicket.Status.CLOSED)
            for ticket in open_tickets:
                if dry_run:
                    self.stdout.write(f"would refresh {ticket.reference}")
                    continue
                try:
                    whisper360.refresh_ticket(ticket)
                    refreshed += 1
                except whisper360.Whisper360Error as exc:
                    refresh_failed += 1
                    self.stderr.write(f"{ticket.reference}: {exc}")

        self.stdout.write(
            f"pushed {pushed}, push failed {failed}, "
            f"refreshed {refreshed}, refresh failed {refresh_failed}"
        )
