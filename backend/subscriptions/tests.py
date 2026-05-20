from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from authentication.models import User
from dispatcher.models import Merchant, Rider
from orders.models import Order, Vehicle
from subscriptions.models import (
    SubscriptionPlan,
    MerchantSubscription,
    SubscriptionUsage,
    SubscriptionOverage,
    SubscriptionInvoice,
)
from subscriptions.services import process_order_subscription, generate_end_of_period_invoice
from wallet.models import Wallet

class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="merchant@example.com",
            password="password123",
            business_name="Test Merchant",
            usertype="Merchant"
        )
        self.merchant = Merchant.objects.get(user=self.user)
        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.balance = Decimal("10000.00")
        self.wallet.save()
        
        self.vehicle = Vehicle.objects.create(
            name="Bike",
            base_price=Decimal("500.00"),
            base_fare=500,
            max_weight_kg=10
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name="Basic Plan",
            price=Decimal("5000.00"),
            free_orders_limit=2,
            overage_fee=Decimal("100.00"),
            has_dedicated_rider=False
        )
        
        self.subscription = MerchantSubscription.objects.create(
            merchant=self.merchant,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
            status="active"
        )

    def test_usage_tracking_and_overage(self):
        # Order 1 (Free)
        order1 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        process_order_subscription(order1)
        self.assertEqual(order1.total_amount, Decimal("0.00"))
        usage = SubscriptionUsage.objects.get(subscription=self.subscription)
        self.assertEqual(usage.used_free_orders, 1)

        # Order 2 (Free)
        order2 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        process_order_subscription(order2)
        self.assertEqual(order2.total_amount, Decimal("0.00"))
        usage.refresh_from_db()
        self.assertEqual(usage.used_free_orders, 2)

        # Order 3 (Overage)
        order3 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        process_order_subscription(order3)
        self.assertEqual(order3.total_amount, Decimal("0.00")) # Deferred
        overage = SubscriptionOverage.objects.get(order=order3)
        self.assertEqual(overage.amount, self.plan.overage_fee)

    def test_invoice_generation(self):
        # Create 2 overages
        order1 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        subscription_usage = SubscriptionUsage.objects.create(
            subscription=self.subscription,
            cycle_start_date=self.subscription.start_date.date(),
            cycle_end_date=self.subscription.end_date.date(),
            used_free_orders=2
        )
        
        order2 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        process_order_subscription(order2) # Overage 1
        
        order3 = Order.objects.create(user=self.user, vehicle=self.vehicle, total_amount=Decimal("500.00"))
        process_order_subscription(order3) # Overage 2
        
        invoice = generate_end_of_period_invoice(self.subscription)
        
        expected_overage = self.plan.overage_fee * 2
        expected_total = self.plan.price + expected_overage
        
        self.assertEqual(invoice.plan_amount, self.plan.price)
        self.assertEqual(invoice.total_overage_amount, expected_overage)
        self.assertEqual(invoice.total_amount, expected_total)
