from rest_framework import viewsets, permissions
from .models import Rider
from .serializers import RiderSerializer


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all().select_related("user", "vehicle_type")
    serializer_class = RiderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally filter by status or checks
        return super().get_queryset()
