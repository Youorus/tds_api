import pytest
from api.leads.models import Lead
from api.clients.models import Client
from api.statut_dossier.models import StatutDossier
from api.lead_status.models import LeadStatus

@pytest.fixture
def statut_dossier(db):
    return StatutDossier.objects.create(
        code="NOUVEAU",
        label="Nouveau",
        color="#C1E8FF"
    )

@pytest.fixture
def lead_status(db):
    return LeadStatus.objects.create(
        code="NOUVEAU",
        label="Nouveau",
        color="#C1E8FF"
    )

@pytest.fixture
def lead(db, statut_dossier, lead_status):
    return Lead.objects.create(
        first_name="Marc",
        last_name="Nkue",
        phone="0601020304",
        email="marc@example.com",
        status=lead_status,
        statut_dossier=statut_dossier,
    )

@pytest.mark.django_db
class TestClientModel:
    def test_create_client_minimal(self, lead):
        client = Client.objects.create(lead=lead)
        assert client.pk is not None

    def test_unique_lead_constraint(self, lead):
        Client.objects.create(lead=lead)
        with pytest.raises(Exception):
            Client.objects.create(lead=lead)

    def test_str_representation(self, lead):
        client = Client.objects.create(lead=lead)
        assert str(client) == "Données de Marc Nkue"

    def test_defaults_and_types(self, lead):
        client = Client.objects.create(lead=lead)
        assert isinstance(client.source, list)
        assert client.custom_demande == ""
        assert client.a_un_visa is None

    def test_foreign_keys(self, lead):
        client = Client.objects.create(lead=lead)
        assert client.lead == lead