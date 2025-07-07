# api/leads/tests/test_lead_status_serializer.py
import pytest
from api.models import LeadStatus
from api.leads.serializers import LeadStatusSerializer
from api.leads.constants import RDV_CONFIRME

@pytest.mark.django_db
def test_lead_status_serializer_output():
    status = LeadStatus.objects.create(
        code=RDV_CONFIRME,
        label="RDV Confirmé",
        color="#00FF00"
    )
    serializer = LeadStatusSerializer(status)
    data = serializer.data
    assert data["code"] == RDV_CONFIRME
    assert data["label"] == "RDV Confirmé"
    assert data["color"] == "#00FF00"
    assert "id" in data