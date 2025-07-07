import pytest
from api.statut_dossiers.models import StatutDossier

@pytest.mark.django_db
def test_statut_dossier_creation():
    sd = StatutDossier.objects.create(code="COMPLET", label="Dossier complet", color="#00FF00")
    assert str(sd) == "Dossier complet (COMPLET)"
    assert sd.code == "COMPLET"
    assert sd.label == "Dossier complet"
    assert sd.color == "#00FF00"