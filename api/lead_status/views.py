from rest_framework import viewsets

from api.lead_status.models import LeadStatus
from api.lead_status.serializer import LeadStatusSerializer


class LeadStatusViewSet(viewsets.ModelViewSet):
    queryset = LeadStatus.objects.all()
    serializer_class = LeadStatusSerializer