from rest_framework import viewsets
from api.models import LeadStatus
from api.serializers.Lead_status_serializer import LeadStatusSerializer


class LeadStatusViewSet(viewsets.ModelViewSet):
    queryset = LeadStatus.objects.all()
    serializer_class = LeadStatusSerializer
    # permissions selon rôle ici