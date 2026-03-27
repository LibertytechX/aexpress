from rest_framework.permissions import BasePermission


class HasOCCReadScope(BasePermission):
    """Allows access if the service key has 'occ:read' or 'occ:*' scope."""

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "scopes"):
            return "occ:read" in user.scopes or "occ:*" in user.scopes
        return False


class HasOCCWriteScope(BasePermission):
    """Allows access if the service key has 'occ:write' or 'occ:*' scope."""

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "scopes"):
            return "occ:write" in user.scopes or "occ:*" in user.scopes
        return False


class IsDispatcher(BasePermission):
    """
    Permission class for if the authenticated user is a dispatcher
    """

    def has_permission(self, request, view):
        # should have a dispatcher profile
        user = request.user
        return hasattr(user, "dispatcher_profile")


class IsZoneLead(BasePermission):
    """
    Permission class for if the authenticated user is a zone lead and a dispatcher
    """

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "dispatcher_profile"):
            return user.dispatcher_profile.role == "zone_lead"
        return False


class IsDispatcherAdmin(BasePermission):
    """
    Permission class for the authenticated dispatcher is an admin dispatcher
    """

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "dispatcher_profile"):
            return user.dispatcher_profile.role == "admin"
        return False


class IsMerchant(BasePermission):
    """
    Permission class for merchant only resources
    """

    def has_permission(self, request, view):
        user = request.user
        return hasattr(user, "merchant_profile")
