import pytest
from api.models import LeadStatus
from api.leads.constants import RDV_CONFIRME, RDV_PLANIFIE, ABSENT, PRESENT

@pytest.mark.django_db
def test_lead_status_creation():
    """Teste la création d’un statut de lead avec les constantes."""
    status = LeadStatus.objects.create(
        code=RDV_CONFIRME,
        label="RDV Confirmé",
        color="#00FF00"
    )
    assert status.code == RDV_CONFIRME
    assert status.label == "RDV Confirmé"
    assert status.color == "#00FF00"
    assert str(status) == "RDV Confirmé"

@pytest.mark.django_db
def test_lead_status_code_uniqueness():
    """Teste l’unicité du code via les constantes."""
    LeadStatus.objects.create(code=RDV_PLANIFIE, label="Planifié", color="#123456")
    with pytest.raises(Exception):
        LeadStatus.objects.create(code=RDV_PLANIFIE, label="Encore planifié", color="#654321")

@pytest.mark.django_db
def test_lead_status_default_color():
    """Teste la valeur par défaut du champ color."""
    status = LeadStatus.objects.create(code=ABSENT, label="Absent")
    assert status.color == "#333333"

@pytest.mark.django_db
def test_lead_status_str_display():
    """Teste l’affichage __str__ du statut."""
    status = LeadStatus.objects.create(code=PRESENT, label="À afficher", color="#ABCDEF")
    assert str(status) == "À afficher"