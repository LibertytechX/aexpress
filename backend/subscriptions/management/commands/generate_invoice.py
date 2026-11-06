from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from subscriptions.models import MerchantPostpaidSubscription, MerchantSubscription
from dispatcher.models import Merchant
from subscriptions.services import generate_postpaid_invoice, generate_end_of_period_invoice


class Command(BaseCommand):
    help = "Generate invoice for a postpaid plan or subscription"

    def add_arguments(self, parser):
        parser.add_argument(
            "merchant_identifier", type=str, help="Merchant ID, phone, or business name"
        )
        parser.add_argument(
            "--type",
            type=str,
            choices=["postpaid", "subscription"],
            required=True,
            help="Type of invoice to generate",
        )

    def handle(self, *args, **options):
        identifier = options["merchant_identifier"]
        invoice_type = options["type"]

        merchant = (
            Merchant.objects.filter(
                Q(merchant_id=identifier)
                | Q(user__phone=identifier)
                | Q(user__business_name__icontains=identifier)
            )
            .select_related("user")
            .first()
        )

        if not merchant:
            raise CommandError(f"Merchant '{identifier}' not found.")

        try:
            if invoice_type == "postpaid":
                sub = MerchantPostpaidSubscription.objects.filter(
                    merchant=merchant, status__in=["active", "blocked"]
                ).first()
                if not sub:
                    raise CommandError(
                        f"No active postpaid subscription for merchant {merchant.user.business_name}."
                    )

                invoice = generate_postpaid_invoice(sub)
                if invoice:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully generated postpaid invoice {invoice.id} for {invoice.amount}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "No accumulation found for postpaid plan. Period rotated without invoice."
                        )
                    )

            elif invoice_type == "subscription":
                sub = MerchantSubscription.objects.filter(
                    merchant=merchant, status="active"
                ).first()
                if not sub:
                    raise CommandError(
                        f"No active subscription for merchant {merchant.user.business_name}."
                    )

                invoice = generate_end_of_period_invoice(sub)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully generated subscription invoice {invoice.id} for {invoice.total_amount}"
                    )
                )

        except Exception as e:
            raise CommandError(f"Error generating invoice: {str(e)}")
