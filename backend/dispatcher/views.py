from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Rider
from .serializers import RiderSerializer
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all().select_related("user", "vehicle_type")
    serializer_class = RiderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally filter by status or checks
        return super().get_queryset()
        return super().get_queryset()


class OrderViewSet(viewsets.ModelViewSet):
    from orders.models import Order

    queryset = (
        Order.objects.all()
        .select_related("user", "rider", "rider__user")
        .prefetch_related("deliveries")
    )
    from .serializers import OrderSerializer

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")


class MerchantViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(usertype="Merchant")
    from .serializers import MerchantSerializer

    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")
