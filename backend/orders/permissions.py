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
