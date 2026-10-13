from rest_framework.permissions import BasePermission


class IsDriver(BasePermission):
    """
    Allows access only to authenticated riders.
    Uses dispatcher.Rider model relation.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rider_profile")
        )


IsRider = IsDriver


class IsVerifiedRider(BasePermission):
    """
    Allows access only to authenticated riders who are authorized
    and verified (especially independent riders whose KYC has been approved).
    """

    message = "Account is not verified or authorized. You cannot access order offers until approved."

    def has_permission(self, request, view):
        if not (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rider_profile")
        ):
            return False

        rider = request.user.rider_profile
        if not rider.is_authorized:
            return False
        if (
            rider.is_independent_rider
            and getattr(rider, "approval_status", "") != "approved"
        ):
            return False
        return True
