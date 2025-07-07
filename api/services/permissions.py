from rest_framework.permissions import BasePermission

class IsServiceAdminOrReadOnly(BasePermission):
    """
    Permission personnalisée pour les services :
    - Lecture ouverte à tous.
    - Création, modification et suppression réservées aux admins.
    """

    def has_permission(self, request, view):
        # Lecture autorisée à tous
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Modification/restreinte aux admins
        return request.user and request.user.is_authenticated and request.user.is_staff