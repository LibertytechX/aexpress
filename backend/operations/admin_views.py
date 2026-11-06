from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from dispatcher.models import RelayNode, Rider, VerticalLead, Zone, ZoneCaptain, ZoneTarget

from .permissions import IsOperationsAdmin
from .serializers import (
    AdminHubSerializer,
    AdminZoneSerializer,
    AdminZoneTargetSerializer,
    RiderHubAssignmentSerializer,
    RiderHubSerializer,
    VerticalLeadAssignmentSerializer,
    VerticalLeadSerializer,
    ZoneCaptainAssignmentSerializer,
    ZoneCaptainSerializer,
)


class AdminZoneListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminZoneSerializer

    def get_queryset(self):
        qs = Zone.objects.select_related("vertical", "zone_lead", "zone_lead__user").order_by("name")
        vertical_id = self.request.query_params.get("vertical")
        if vertical_id:
            qs = qs.filter(vertical_id=vertical_id)
        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ("true", "1", "yes"))
        return qs


class AdminZoneDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminZoneSerializer
    queryset = Zone.objects.select_related("vertical", "zone_lead", "zone_lead__user")


class AdminHubListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminHubSerializer

    def get_queryset(self):
        qs = RelayNode.objects.select_related("zone", "zone__vertical").order_by("name")
        zone_id = self.request.query_params.get("zone")
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ("true", "1", "yes"))
        return qs


class AdminHubDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminHubSerializer
    queryset = RelayNode.objects.select_related("zone", "zone__vertical")


class AdminZoneTargetListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminZoneTargetSerializer

    def get_queryset(self):
        qs = ZoneTarget.objects.select_related("zone").order_by("-month", "zone__name")
        zone_id = self.request.query_params.get("zone")
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        month = self.request.query_params.get("month")
        if month:
            try:
                from datetime import datetime

                qs = qs.filter(month=datetime.strptime(month, "%Y-%m-%d").date().replace(day=1))
            except ValueError:
                pass
        return qs


class AdminZoneTargetDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOperationsAdmin]
    serializer_class = AdminZoneTargetSerializer
    queryset = ZoneTarget.objects.select_related("zone")


class AdminVerticalLeadListAssignView(APIView):
    permission_classes = [IsOperationsAdmin]

    def get(self, request):
        qs = VerticalLead.objects.select_related("user", "vertical").order_by("vertical__code")
        serializer = VerticalLeadSerializer(qs, many=True)
        return Response({"results": serializer.data})

    def post(self, request):
        serializer = VerticalLeadAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            lead = serializer.save()
            return Response(VerticalLeadSerializer(lead).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminVerticalLeadDetailView(APIView):
    permission_classes = [IsOperationsAdmin]

    def patch(self, request, pk):
        lead = get_object_or_404(VerticalLead.objects.select_related("user", "vertical"), pk=pk)
        data = {
            "user": request.data.get("user", lead.user_id),
            "vertical": request.data.get("vertical", lead.vertical_id),
            "is_active": request.data.get("is_active", lead.is_active),
        }
        serializer = VerticalLeadAssignmentSerializer(data=data)
        if serializer.is_valid():
            lead = serializer.save()
            return Response(VerticalLeadSerializer(lead).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminZoneCaptainListAssignView(APIView):
    permission_classes = [IsOperationsAdmin]

    def get(self, request):
        qs = ZoneCaptain.objects.select_related("user", "zone").order_by("zone__name")
        serializer = ZoneCaptainSerializer(qs, many=True)
        return Response({"results": serializer.data})

    def post(self, request):
        serializer = ZoneCaptainAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            captain = serializer.save()
            return Response(ZoneCaptainSerializer(captain).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminZoneCaptainDetailView(APIView):
    permission_classes = [IsOperationsAdmin]

    def patch(self, request, pk):
        captain = get_object_or_404(ZoneCaptain.objects.select_related("user", "zone"), pk=pk)
        data = {
            "user": request.data.get("user", captain.user_id),
            "zone": request.data.get("zone", captain.zone_id),
            "is_active": request.data.get("is_active", captain.is_active),
        }
        serializer = ZoneCaptainAssignmentSerializer(data=data)
        if serializer.is_valid():
            captain = serializer.save()
            return Response(ZoneCaptainSerializer(captain).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminRiderAssignHubView(APIView):
    permission_classes = [IsOperationsAdmin]

    def patch(self, request, pk):
        rider = get_object_or_404(
            Rider.objects.select_related("user", "hub", "hub__zone"),
            pk=pk,
        )
        serializer = RiderHubAssignmentSerializer(
            data=request.data,
            context={"rider": rider},
        )
        if serializer.is_valid():
            rider = serializer.save()
            return Response(RiderHubSerializer(rider).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
