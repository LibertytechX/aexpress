import pytest
from decimal import Decimal
from datetime import datetime, timedelta, time
from django.utils import timezone
from authentication.models import User
from dispatcher.models import VehicleAsset, Rider, VehicleTracking
from dispatcher.serializers import VehicleAssetSerializer
from orders.models import Order, Vehicle


@pytest.mark.django_db
class TestVehicleAssetOptimization:

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

        # Create 3 VehicleAssets
        self.assets = [
            VehicleAsset.objects.create(
                plate_number=f"LAG-00{i}-AB",
                vehicle_type=VehicleAsset.VehicleType.BIKE,
            )
            for i in range(3)
        ]

        # Create Riders assigned to assets
        self.riders = []
        for i in range(2):
            u = User.objects.create_user(
                phone=f"+234802222000{i}",
                password="password123",
                first_name="Rider",
                last_name=str(i),
                usertype="Rider",
            )
            r = Rider.objects.get(user=u)
            r.vehicle_asset = self.assets[i]
            r.save()
            self.riders.append(r)

        merchant_user = User.objects.create_user(
            phone="+2348033330000",
            email="merchant@test.com",
            password="password123",
            usertype="Merchant",
        )

        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # Orders for Rider 0 (Asset 0):
        # 1 today, 1 yesterday
        Order.objects.create(
            order_number="ORD-V-001",
            user=merchant_user,
            rider=self.riders[0],
            vehicle=self.vehicle,
            pickup_address="A",
            total_amount=1000,
            distance_km=5.5,
            status="Done",
            completed_at=now,
        )
        Order.objects.create(
            order_number="ORD-V-002",
            user=merchant_user,
            rider=self.riders[0],
            vehicle=self.vehicle,
            pickup_address="A",
            total_amount=1000,
            distance_km=10.2,
            status="Done",
            completed_at=yesterday,
        )

        # VehicleTracking for Asset 0 yesterday
        today = timezone.localdate()
        tz = timezone.get_current_timezone()
        yesterday_mid = timezone.make_aware(
            datetime.combine(today - timedelta(days=1), time(12, 0)), tz
        )

        vt1 = VehicleTracking.objects.create(
            vehicle_asset=self.assets[0],
            latitude=6.5244,
            longitude=3.3792,
            travelled=Decimal("100.00"),
        )
        VehicleTracking.objects.filter(id=vt1.id).update(
            created_at=yesterday_mid - timedelta(hours=2)
        )

        vt2 = VehicleTracking.objects.create(
            vehicle_asset=self.assets[0],
            latitude=6.5244,
            longitude=3.3792,
            travelled=Decimal("125.50"),
        )
        VehicleTracking.objects.filter(id=vt2.id).update(
            created_at=yesterday_mid + timedelta(hours=2)
        )

    def test_batch_serialization_constant_queries(self, django_assert_max_num_queries):
        """Batch serialization across assets runs in bounded queries (no N+1)."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        from dispatcher.views import VehicleAssetViewSet

        view = VehicleAssetViewSet()
        factory = APIRequestFactory()
        view.request = Request(factory.get("/api/dispatch/vehicle-assets/"))

        # Query 1: VehicleAsset
        # Query 2: Riders prefetch with user select_related
        # Query 3: Orders today batch
        # Query 4: Orders yesterday batch
        # Query 5-6: VehicleTracking first/last batch if uncached
        with django_assert_max_num_queries(6):
            qs = view.get_queryset().filter(id__in=[a.id for a in self.assets])
            data = VehicleAssetSerializer(qs, many=True).data

        assert len(data) == 3
        data_by_id = {item["id"]: item for item in data}

        a0_data = data_by_id[str(self.assets[0].id)]
        assert a0_data["orders_today"] == 1
        assert a0_data["yesterday_orders"] == 1
        assert a0_data["total_yesterday_orders_distance_km"] == 10.2
        assert a0_data["yesterday_distance"] == Decimal("25.50") or a0_data["yesterday_distance"] == 25.5

        a1_data = data_by_id[str(self.assets[1].id)]
        assert a1_data["orders_today"] == 0
        assert a1_data["yesterday_orders"] == 0

        a2_data = data_by_id[str(self.assets[2].id)]
        assert a2_data["orders_today"] == 0

    def test_single_asset_fallback(self):
        """Serializing a single asset without many=True works correctly."""
        data = VehicleAssetSerializer(self.assets[0]).data
        assert data["orders_today"] == 1
        assert data["yesterday_orders"] == 1
        assert data["total_yesterday_orders_distance_km"] == 10.2
