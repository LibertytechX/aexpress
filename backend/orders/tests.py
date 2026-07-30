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
)
from orders.admin import (
    MerchantPricingOverrideAdmin,
    MerchantPriceListAdmin,
    MerchantPriceListItemAdmin,
    OrderAdmin,
    DeliveryAdmin,
    OrderLegAdmin,
    OrderEventAdmin,
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


from django.contrib.auth import get_user_model
from wallet.models import Charge
from orders.tasks import create_order_charge
from orders.models import Vehicle
import uuid
from decimal import Decimal

User = get_user_model()


class CreateOrderChargeTaskTest(TestCase):
    """Test suite for the create_order_charge celery task."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            phone="+2348000000001",
            email="test_user@example.com",
            password="test_password",
            usertype="Merchant",
        )
        self.vehicle = Vehicle.objects.create(
            name="Test Bike",
            max_weight_kg=50,
            base_price=300,
            base_fare=300,
            rate_per_km=40,
            rate_per_minute=2,
            is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            pickup_address="123 Test Street",
            total_amount=Decimal("1500.00"),
            distance_km=Decimal("10.0"),
            duration_minutes=30,
        )

    def test_create_order_charge_success(self) -> None:
        """Verify that the task successfully creates a charge and returns its ID."""
        charge_id_str = create_order_charge(str(self.order.id))

        # Check that it returns a valid UUID string
        self.assertIsInstance(charge_id_str, str)
        charge_uuid = uuid.UUID(charge_id_str)
        self.assertEqual(str(charge_uuid), charge_id_str)

        # Verify charge is created in DB with correct values
        charge = Charge.objects.get(id=charge_uuid)
        self.assertEqual(charge.user, self.user)
        self.assertEqual(charge.order, self.order)
        self.assertEqual(charge.amount, self.order.total_amount)
        self.assertEqual(charge.status, "pending")

    def test_create_order_charge_order_not_found(self) -> None:
        """Verify that the task raises Order.DoesNotExist if the order doesn't exist."""
        random_uuid = str(uuid.uuid4())
        with self.assertRaises(Order.DoesNotExist):
            create_order_charge(random_uuid)

