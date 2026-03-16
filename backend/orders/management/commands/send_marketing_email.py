import os
from django.core.management.base import BaseCommand, CommandError
from authentication.models import User
from orders.marketing_tasks import _send_marketing_email

class Command(BaseCommand):
    help = 'Sends a specific marketing email template to a merchant by their phone number'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='The phone number of the merchant')
        parser.add_argument('template_code', type=str, help='The code of the marketing template to send (e.g. A2, C1, E1)')
        
        # Optional arguments
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending the email even if it was already sent (ignores idempotency check in some cases)',
        )

    def handle(self, *args, **options):
        phone = options['phone']
        template_code = options['template_code'].upper()
        
        try:
            merchant = User.objects.get(phone=phone, usertype="Merchant")
        except User.DoesNotExist:
            raise CommandError(f'Merchant with phone "{phone}" does not exist.')
            
        self.stdout.write(self.style.WARNING(f'Attempting to send {template_code} to {merchant.first_name or merchant.contact_name} ({phone})...'))
        
        # We define a basic catch-all subject mapping for testing
        # Transactional emails normally require an order context. We'll provide a dummy one if it's F1 or F2.
        subject_map = {
            "A1": "Welcome to Assured Express 🎉",
            "A2": "Complete your setup on Assured Express in 2 minutes",
            "B1": f"Your first delivery is waiting, {merchant.first_name or merchant.contact_name or 'there'} Let's get moving! 🚚",
            "B2A": f"We miss you, {merchant.first_name or merchant.contact_name or 'there'} 👋",
            "B2B": f"What's stopping you, {merchant.first_name or merchant.contact_name or 'there'}? Let's fix it together 🤝",
            "B2C": f"{merchant.first_name or merchant.contact_name or 'Merchant'} — your account is ready when you are",
            "C1": "The Merchant, and how delivery changed everything",
            "C2": "Your customers judge you by your delivery. 📦",
            "D1": "Big news: We're bringing POS terminals to your doorstep! 💳",
            "D2": "Capital when you need it most — no collateral, no stress 💼",
            "D3": "Stop guessing — start knowing your numbers 📊",
            "E1": "Your Weekly Delivery Report 📊",
            "E2": "See What You're Missing This Week on Assured Express 👀",
            "F1": "Your delivery is on the move! 🚚",
            "F2": "✅ Delivery Completed! has arrived"
        }
        
        subject = subject_map.get(template_code, f"Assured Express: {template_code}")
        
        context = {}
        
        # Dummy context for specific templates if needed during manual test
        if template_code.startswith("E") and template_code == "E1":
            context = {
                "start_date": "Test Start",
                "end_date": "Test End",
                "total_requested": 10,
                "total_delivered": 9,
                "success_rate": 90,
                "most_active_day": "Monday",
                "top_delivery_zone": "Lagos Island",
            }
        elif template_code.startswith("F"):
            # Provide dummy object interfaces for order and delivery to prevent template errors
            class DummyOrder:
                order_number = "TEST-123"
                notes = "Test Package"
                pickup_address = "Test Pickup"
                class _Rider:
                    class _User:
                        def get_full_name(self): return "Test Rider"
                        phone = "0000000000"
                    user = _User()
                rider = _Rider()
            class DummyDelivery:
                dropoff_address = "Test Dropoff"
                
            context = {
                "order": DummyOrder(),
                "delivery": DummyDelivery()
            }
            
        success = _send_marketing_email(merchant, template_code, subject, context)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Successfully sent template "{template_code}" to merchant {phone}.'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send template "{template_code}" to merchant {phone}. Note: it may have already been sent. Check the logs.'))
