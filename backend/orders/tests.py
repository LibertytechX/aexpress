from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from orders.models import (
    MerchantPricingOverride,
    MerchantPriceList,
    MerchantPriceListItem,
    Order,
    Delivery,
    OrderLeg,
)
from orders.admin import (
    MerchantPricingOverrideAdmin,
    MerchantPriceListAdmin,
    MerchantPriceListItemAdmin,
    OrderAdmin,
    DeliveryAdmin,
    OrderLegAdmin,
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
