"""Unit tests for Orders Django Admin model configurations."""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from orders.models import (
    MerchantPricingOverride,
    MerchantPriceList,
    MerchantPriceListItem,
    Order,
    Delivery,
    OrderLeg,
    OrderEvent,
    GoogleAutoCompleteSessionUsage,
    GooglePlace,
)
from orders.admin import (
    MerchantPricingOverrideAdmin,
    MerchantPriceListAdmin,
    MerchantPriceListItemAdmin,
    OrderAdmin,
    DeliveryAdmin,
    OrderLegAdmin,
    OrderEventAdmin,
    GoogleAutoCompleteSessionUsageAdmin,
    GooglePlaceAdmin,
)


class OrdersAdminRawIdFieldsTest(TestCase):
    """Test suite to verify that orders admin models have raw_id_fields optimized."""

    def test_raw_id_fields_configured(self) -> None:
        """Verify that foreign key fields are optimized to use raw_id_fields."""
        site = AdminSite()

        override_admin = MerchantPricingOverrideAdmin(MerchantPricingOverride, site)
        self.assertIn("merchant", override_admin.raw_id_fields)

        pricelist_admin = MerchantPriceListAdmin(MerchantPriceList, site)
        self.assertIn("merchant", pricelist_admin.raw_id_fields)

        item_admin = MerchantPriceListItemAdmin(MerchantPriceListItem, site)
        self.assertIn("price_list", item_admin.raw_id_fields)

        order_admin = OrderAdmin(Order, site)
        self.assertIn("user", order_admin.raw_id_fields)
        self.assertIn("rider", order_admin.raw_id_fields)
        self.assertIn("parent_order", order_admin.raw_id_fields)
        self.assertIn("suggested_rider", order_admin.raw_id_fields)

        delivery_admin = DeliveryAdmin(Delivery, site)
        self.assertIn("order", delivery_admin.raw_id_fields)

        leg_admin = OrderLegAdmin(OrderLeg, site)
        self.assertIn("order", leg_admin.raw_id_fields)
        self.assertIn("rider", leg_admin.raw_id_fields)
        self.assertIn("suggested_rider", leg_admin.raw_id_fields)

        event_admin = OrderEventAdmin(OrderEvent, site)
        self.assertIn("order", event_admin.raw_id_fields)
        self.assertIn("created_by", event_admin.raw_id_fields)

        session_usage_admin = GoogleAutoCompleteSessionUsageAdmin(
            GoogleAutoCompleteSessionUsage, site
        )
        self.assertIn("user", session_usage_admin.raw_id_fields)
        self.assertIn("session_token", session_usage_admin.list_display)
        self.assertIn("status", session_usage_admin.list_filter)

        place_admin = GooglePlaceAdmin(GooglePlace, site)
        self.assertIn("place_id", place_admin.list_display)
        self.assertIn("formatted_address", place_admin.search_fields)

