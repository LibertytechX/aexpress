from rest_framework.permissions import BasePermission


class IsOperationsAdmin(BasePermission):
    """Allow only COO/admin users to manage operations dashboard structure."""

    def has_permission(self, request, view):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_superuser", False):
            return True
        dispatcher_profile = getattr(user, "dispatcher_profile", None)
        return bool(dispatcher_profile and dispatcher_profile.role == "admin")
