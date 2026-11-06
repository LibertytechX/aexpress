"""
Run the alert engine once (manual / debugging).

Usage:
    python manage.py run_alert_engine
    python manage.py run_alert_engine --type BIKE_AFTER_HOURS --type INCOMPLETE_ORDER
"""

from django.core.management.base import BaseCommand

from oprtn_dashboard.alerts.engine import run_all_rules


class Command(BaseCommand):
    help = "Evaluate enabled alert rules and reconcile alerts once."

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            action="append",
            dest="types",
            help="Limit to one or more alert_type values (repeatable).",
        )

    def handle(self, *args, **options):
        summary = run_all_rules(only_types=options.get("types"))
        self.stdout.write(
            self.style.SUCCESS(
                "Alert engine run — "
                f"evaluated: {summary['evaluated']}, "
                f"created: {summary['created']}, "
                f"updated: {summary['updated']}, "
                f"resolved: {summary['resolved']}, "
                f"skipped: {summary['skipped']}"
            )
        )
        if summary["no_evaluator"]:
            self.stdout.write(
                f"  (no evaluator yet for: {', '.join(summary['no_evaluator'])})"
            )
