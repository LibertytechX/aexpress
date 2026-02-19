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
    from .serializers import OrderSerializer, OrderCreateSerializer

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return self.OrderCreateSerializer
        return self.OrderSerializer

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")

    from rest_framework.decorators import action

    @action(detail=True, methods=["post"])
    def assign_rider(self, request, order_number=None):
        order = self.get_object()
        rider_id = request.data.get("rider_id")

        if not rider_id:
            # If rider_id is empty/null, it might be an unassign request
            order.rider = None
            order.status = "Pending"
            order.save()
            return Response(self.get_serializer(order).data)

        try:
            rider = Rider.objects.get(
                rider_id=rider_id
            )  # Should use correct lookup field if different
            order.rider = rider
            order.status = "Assigned"
            order.save()
            return Response(self.get_serializer(order).data)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
            )


class MerchantViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(usertype="Merchant")
    from .serializers import MerchantSerializer

    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")
