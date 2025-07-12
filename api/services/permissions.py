# api/services/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsServiceAdminOrReadOnly(BasePermission):
    """
    Autorise tout le monde en lecture seule, mais seulement les staff pour créer/modifier/supprimer.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        print(f"DEBUG | {request.user.email} | staff={request.user.is_staff} | {request.method}")
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff