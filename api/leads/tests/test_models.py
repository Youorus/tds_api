# leads/tests/test_models.py

import pytest
from django.utils import timezone
from api.models import Lead, LeadStatus, User, StatutDossier

@pytest.mark.django_db
def test_lead_creation_sets_defaults():
    """
    Vérifie qu'un lead est créé avec les valeurs par défaut attendues.
    """
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="RDV planifié")
    user = User.objects.create_user("john@doe.com", "John", "Doe", "secret")
    lead = Lead.objects.create(
        first_name="Alice",
        last_name="Wonderland",
        phone="+33600000001",
        status=status,
        assigned_to=user,
    )
    assert lead.first_name == "Alice"
    assert lead.status == status
    assert lead.assigned_to == user

@pytest.mark.django_db
def test_lead_str_representation():
    """
    Vérifie la représentation textuelle (__str__) du modèle Lead.
    """
    status = LeadStatus.objects.create(code="RDV_PLANIFIE", label="RDV planifié")
    lead = Lead.objects.create(
        first_name="Alice",
        last_name="Wonderland",
        phone="+33600000001",
        status=status,
    )
    assert "Alice Wonderland" in str(lead)
    assert "RDV planifié" in str(lead)