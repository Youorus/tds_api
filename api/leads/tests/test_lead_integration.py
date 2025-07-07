import pytest
from django.utils import timezone
from api.models import Lead, LeadStatus, User
from api.leads.constants import RDV_CONFIRME, RDV_PLANIFIE, ABSENT, PRESENT

@pytest.fixture
def admin_user(db):
    """Crée un utilisateur admin pour l’assignation de leads."""
    return User.objects.create_user(
        email="admin@ex.com",
        first_name="Admin",
        last_name="User",
        password="adminpass",
        role=User.Roles.ADMIN,
    )

@pytest.fixture
def statut_rdv_confirme(db):
    """Crée un statut RDV_CONFIRME."""
    return LeadStatus.objects.create(code=RDV_CONFIRME, label="RDV Confirmé", color="#00FF00")

@pytest.fixture
def statut_rdv_planifie(db):
    """Crée un statut RDV_PLANIFIE."""
    return LeadStatus.objects.create(code=RDV_PLANIFIE, label="RDV Planifié", color="#0000FF")

@pytest.mark.django_db
def test_lead_creation_with_status(statut_rdv_confirme, admin_user):
    """Teste la création d’un lead avec un statut RDV_CONFIRME."""
    lead = Lead.objects.create(
        first_name="John",
        last_name="Doe",
        email="john.doe@email.com",
        phone="+33612345678",
        status=statut_rdv_confirme,
        assigned_to=admin_user,
        created_at=timezone.now(),
    )
    assert lead.status.code == RDV_CONFIRME
    assert lead.assigned_to == admin_user

@pytest.mark.django_db
def test_lead_status_update(statut_rdv_confirme, statut_rdv_planifie, admin_user):
    """Teste la mise à jour du statut d’un lead."""
    lead = Lead.objects.create(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@email.com",
        phone="+33687654321",
        status=statut_rdv_planifie,
        assigned_to=admin_user,
        created_at=timezone.now(),
    )
    assert lead.status.code == RDV_PLANIFIE

    lead.status = statut_rdv_confirme
    lead.save()
    lead.refresh_from_db()
    assert lead.status.code == RDV_CONFIRME

@pytest.mark.django_db
def test_lead_status_required(admin_user):
    """Vérifie qu’un lead ne peut être créé sans statut si la contrainte existe (FK obligatoire)."""
    with pytest.raises(Exception):
        Lead.objects.create(
            first_name="Foo",
            last_name="Bar",
            email="foo.bar@email.com",
            phone="+33765432109",
            assigned_to=admin_user,
            created_at=timezone.now(),
        )

@pytest.mark.django_db
def test_lead_status_integrity(admin_user, statut_rdv_confirme):
    """Vérifie que la suppression d’un statut protégé empêche la suppression s’il est utilisé."""
    lead = Lead.objects.create(
        first_name="Amina",
        last_name="Traoré",
        email="amina.t@email.com",
        phone="+33699998877",
        status=statut_rdv_confirme,
        assigned_to=admin_user,
        created_at=timezone.now(),
    )
    with pytest.raises(Exception):
        # PROTECT devrait empêcher la suppression du statut utilisé
        statut_rdv_confirme.delete()