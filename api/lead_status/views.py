from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.lead_status.models import LeadStatus
from api.lead_status.serializer import LeadStatusSerializer
from api.lead_status.permissions import IsAdminRole

class LeadStatusViewSet(viewsets.ModelViewSet):
    queryset = LeadStatus.objects.all()
    serializer_class = LeadStatusSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminRole()]