from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Autorise uniquement les utilisateurs ayant le rôle 'ADMIN'.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and getattr(user, "role", None) == "ADMIN"