from api.statut_dossiers.models import StatutDossier
from api.statut_dossiers.serializers import StatutDossierSerializer

def test_statut_dossier_serializer():
    sd = StatutDossier(code="A_TRAITER", label="À traiter", color="#ff9900")
    data = StatutDossierSerializer(sd).data
    assert data["code"] == "A_TRAITER"
    assert data["label"] == "À traiter"
    assert data["color"] == "#ff9900"