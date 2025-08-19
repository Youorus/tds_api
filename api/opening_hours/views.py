from rest_framework import viewsets, permissions
from .models import OpeningHours
from .serializers import OpeningHoursSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - GET/HEAD/OPTIONS : tout le monde
    - POST/PUT/PATCH/DELETE : admin seulement
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class OpeningHoursViewSet(viewsets.ModelViewSet):
    queryset = OpeningHours.objects.all().order_by("day_of_week")
    serializer_class = OpeningHoursSerializer
    permission_classes = [IsAdminOrReadOnly]