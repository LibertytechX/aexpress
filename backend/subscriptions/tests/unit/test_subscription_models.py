"""Unit tests for Subscription models and helper calculations."""

from decimal import Decimal
from django.test import TestCase
from subscriptions.models import SubscriptionPlan


class SubscriptionPlanModelUnitTest(TestCase):
    """Unit tests for subscription plan properties."""

    def test_subscription_plan_str(self):
        plan = SubscriptionPlan(name="Starter Plan", price=Decimal("2500.00"))
        self.assertEqual(str(plan), "Starter Plan (₦2500.00)")
