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
