"""
Referral program API views.
All views require rider authentication.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Sum
from decimal import Decimal

from orders.permissions import IsRider
from .models import RiderReferral, ReferralEarning


def get_rider(user):
    """Helper to get rider profile from user."""
    return getattr(user, "rider_profile", None)


class ReferralOverviewView(APIView):
    """
    GET /api/riders/referrals/overview/
    Returns the rider's referral code, total earnings, and high-level stats.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_earnings = ReferralEarning.objects.filter(
            referral__referring_rider=rider
        ).aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00")

        total_referrals = RiderReferral.objects.filter(referring_rider=rider).count()
        active_referrals = RiderReferral.objects.filter(
            referring_rider=rider, status=RiderReferral.Status.ACTIVE
        ).count()

        return Response(
            {
                "referral_code": rider.referral_code,
                "total_earnings": total_earnings,
                "total_referrals": total_referrals,
                "active_referrals": active_referrals,
                "commission_rate": "5%",
                "share_message": (
                    f"Join Axpress and ship your products with ease! "
                    f"Use my referral code {rider.referral_code} when signing up. "
                    f"Link: https://send.axpress.net/?ref={rider.referral_code}"
                ),
            }
        )


class ReferralBusinessListView(APIView):
    """
    GET /api/riders/referrals/businesses/
    Returns the list of businesses referred by this rider with per-business stats.
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        referrals = (
            RiderReferral.objects.filter(referring_rider=rider)
            .select_related("merchant")
            .order_by("-created_at")
        )

        result = []
        for ref in referrals:
            monthly_stats = ref.get_monthly_stats()
            result.append(
                {
                    "id": str(ref.id),
                    "business_name": ref.merchant.business_name,
                    "status": ref.status,
                    "created_at": ref.created_at,
                    "activated_at": ref.activated_at,
                    "orders_this_month": monthly_stats["orders_this_month"],
                    "earnings_this_month": monthly_stats["earnings_this_month"],
                }
            )

        return Response({"businesses": result})


class RegisterReferralBusinessView(APIView):
    """
    POST /api/riders/referrals/register-business/
    Rider submits a quick registration form for a new business they are referring.
    This creates a stub merchant record linked to the rider's referral.

    ...
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def post(self, request):
        rider = get_rider(request.user)
        if not rider:
            return Response(
                {"success": False, "message": "Rider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = request.data

        business_name = data.get("business_name", "").strip()
        contact_phone = data.get("contact_phone", "").strip()
        address = data.get("address", "").strip()

        if not business_name or not contact_phone:
            return Response(
                {"error": "business_name and contact_phone are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if this phone is already a registered user
        from django.contrib.auth import get_user_model

        User = get_user_model()

        existing = User.objects.filter(phone=contact_phone).first()

        if existing:
            # Link to existing user if not already referred
            if RiderReferral.objects.filter(
                referring_rider=rider, merchant=existing
            ).exists():
                return Response(
                    {"error": "You have already referred this business."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            referral = RiderReferral.objects.create(
                referring_rider=rider,
                merchant=existing,
                status=RiderReferral.Status.PENDING,
            )
            return Response(
                {
                    "message": "Business linked to your referral. You will earn commission on their orders.",
                    "referral_id": str(referral.id),
                    "business_name": existing.business_name,
                    "status": referral.status,
                },
                status=status.HTTP_201_CREATED,
            )

        # Create a stub/pending merchant user
        from django.utils.crypto import get_random_string

        temp_password = get_random_string(12)
        new_user = User.objects.create_user(
            phone=contact_phone,
            business_name=business_name,
            address=address,
            password=temp_password,
            is_active=False,  # Not yet activated — they must verify themselves
        )

        referral = RiderReferral.objects.create(
            referring_rider=rider,
            merchant=new_user,
            status=RiderReferral.Status.PENDING,
        )

        return Response(
            {
                "message": (
                    f"{business_name} has been registered. "
                    f"They will need to verify their account to start placing orders."
                ),
                "referral_id": str(referral.id),
                "business_name": business_name,
                "status": referral.status,
            },
            status=status.HTTP_201_CREATED,
        )
