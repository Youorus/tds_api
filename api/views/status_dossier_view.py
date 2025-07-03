from rest_framework import viewsets

from api.models import StatutDossier
from api.serializers.status_dossier_serializer import StatutDossierSerializer


class StatusDossierViewSet(viewsets.ModelViewSet):
    queryset = StatutDossier.objects.all()
    serializer_class = StatutDossierSerializer
    # Ajoute permissions selon ton besoin