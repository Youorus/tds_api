from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminForUnsafeOnly(BasePermission):
    """
    - Lecture (GET, HEAD, OPTIONS) autorisée pour tout le monde
    - Écriture (POST, PUT, DELETE, etc.) uniquement pour les admins
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # lecture publique
        return request.user and request.user.is_authenticated and request.user.is_staff