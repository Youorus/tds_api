# test_views.py
from rest_framework import viewsets
from .models import Service
from .serializers import ServiceSerializer
from .permissions import IsAdminForUnsafeOnly

class ServiceViewSet(viewsets.ModelViewSet):
    """
    - Lecture (GET) accessible à tous
    - Écriture réservée aux admins
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminForUnsafeOnly]