import pytest
from django.utils import timezone
from datetime import timedelta
from authentication.models import User
from dispatcher.models import Merchant
from dispatcher.views import MerchantViewSet
from dispatcher.serializers import MerchantSerializer
from orders.models import Order, Vehicle


@pytest.mark.django_db
class TestMerchantViewSetOptimization:

    @pytest.fixture(autouse=True)
    def setup_entities(self):
        self.vehicle = Vehicle.objects.create(
            name="Motorcycle",
            max_weight_kg=20,
            base_price=500,
            base_fare=500,
            rate_per_km=100,
            rate_per_minute=10,
            min_distance_km=2,
            min_fee=1000,
        )

        # Create 3 Merchants
        self.merchants = []
        for i in range(3):
            u = User.objects.create_user(
                phone=f"+234801111000{i}",
                email=f"merchant{i}@example.com",
                business_name=f"Merchant Biz {i}",
                contact_name=f"Contact {i}",
                password="password123",
                usertype="Merchant",
            )
            self.merchants.append(u)

        now = timezone.now()
        # Merchant 0: 2 orders (1 this month, 1 past month)
        Order.objects.create(
            order_number="ORD-TEST-001",
            user=self.merchants[0],
            vehicle=self.vehicle,
            pickup_address="A",
            total_amount=1000,
            created_at=now,
        )
        old_order = Order.objects.create(
            order_number="ORD-TEST-002",
            user=self.merchants[0],
            vehicle=self.vehicle,
            pickup_address="A",
            total_amount=1000,
        )
        # Shift created_at to 60 days ago
        Order.objects.filter(id=old_order.id).update(created_at=now - timedelta(days=60))

        # Merchant 1: 1 order this month
        Order.objects.create(
            order_number="ORD-TEST-003",
            user=self.merchants[1],
            vehicle=self.vehicle,
            pickup_address="A",
            total_amount=1000,
            created_at=now,
        )

        # Merchant 2: 0 orders

    def test_merchant_viewset_queryset_single_query(self, django_assert_num_queries):
        """Ensure evaluating get_queryset and serializing executes in exactly 1 query."""
        view = MerchantViewSet()
        with django_assert_num_queries(1):
            qs = list(view.get_queryset())
            data = MerchantSerializer(qs, many=True).data

        assert len(data) == 3

        # Map by userId
        data_by_user = {item["userId"]: item for item in data}

        m0_data = data_by_user[str(self.merchants[0].id)]
        assert m0_data["totalOrders"] == 2
        assert m0_data["monthOrders"] == 1

        m1_data = data_by_user[str(self.merchants[1].id)]
        assert m1_data["totalOrders"] == 1
        assert m1_data["monthOrders"] == 1

        m2_data = data_by_user[str(self.merchants[2].id)]
        assert m2_data["totalOrders"] == 0
        assert m2_data["monthOrders"] == 0

    def test_serializer_fallback_without_annotation(self):
        """Ensure serializer falls back cleanly when annotations are not present."""
        m0 = User.objects.get(id=self.merchants[0].id)
        assert not hasattr(m0, "total_orders_count")
        serializer = MerchantSerializer(m0)
        assert serializer.data["totalOrders"] == 2
        assert serializer.data["monthOrders"] == 1
