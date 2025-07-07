from rest_framework import viewsets
from api.services.models import Service
from api.services.serializers import ServiceSerializer
from api.services.permissions import IsServiceAdminOrReadOnly

class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion CRUD des services.
    - Lecture publique (GET/LIST/RETRIEVE)
    - Ajout/modification/suppression réservé aux admins
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsServiceAdminOrReadOnly]