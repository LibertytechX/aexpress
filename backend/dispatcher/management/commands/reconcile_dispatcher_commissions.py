from django.core.management.base import BaseCommand
from dispatcher.models import DispatcherProfile
from dispatcher.services import reconcile_dispatcher_monthly_commission


class Command(BaseCommand):
    help = "Reconciles dispatcher commission entries against monthly earnings summaries and profile caches."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Month to reconcile in YYYY-MM format. Defaults to current active month.",
        )
        parser.add_argument(
            "--dispatcher-id",
            type=str,
            default=None,
            help="Optional UUID of a single dispatcher to reconcile.",
        )

    def handle(self, *args, **options):
        month = options.get("month")
        dispatcher_id = options.get("dispatcher_id")

        if dispatcher_id:
            try:
                dispatchers = [DispatcherProfile.objects.get(id=dispatcher_id)]
            except DispatcherProfile.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Dispatcher with id {dispatcher_id} does not exist."))
                return
        else:
            dispatchers = DispatcherProfile.objects.all()

        self.stdout.write(f"Reconciling {len(dispatchers)} dispatcher(s) for month: {month or 'current'}...")
        for d in dispatchers:
            result = reconcile_dispatcher_monthly_commission(d, month_year=month)
            self.stdout.write(
                f"Dispatcher {d.id} ({d.user.phone}): Month {result['month_year']} -> "
                f"₦{result['total_commission']} ({result['total_orders']} orders), Lifetime: ₦{result['all_time_total']}"
            )

        self.stdout.write(self.style.SUCCESS("Reconciliation completed successfully."))
