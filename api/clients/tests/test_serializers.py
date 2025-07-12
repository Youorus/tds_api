import pytest
from datetime import date, timedelta

from api.clients.serializers import ClientSerializer
from api.leads.models import Lead
from api.lead_status.models import LeadStatus
from api.statut_dossier.models import StatutDossier

@pytest.fixture
def lead_status(db):
    return LeadStatus.objects.create(code="NOUVEAU", label="Nouveau")

@pytest.fixture
def statut_dossier(db):
    return StatutDossier.objects.create(
        code="EN_COURS",
        label="En cours",
        color="#C1E8FF"
    )

@pytest.fixture
def lead(db, lead_status, statut_dossier):
    return Lead.objects.create(
        first_name="Marc",
        last_name="Nkue",
        status=lead_status,
        statut_dossier=statut_dossier,
    )

@pytest.mark.django_db
class TestClientSerializer:
    def test_serializer_accepts_valid_data(self, lead):
        data = {
            "adresse": "1 rue de Paris",
            "ville": "Paris",
            "code_postal": "75000",
            "date_naissance": "1990-01-01",
            "lead": lead.id,  # optionnel selon serializer
        }
        serializer = ClientSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_serializer_refuses_future_birth_date(self, lead):
        future = date.today() + timedelta(days=10)
        data = {
            "date_naissance": future.isoformat(),
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "date_naissance" in serializer.errors

    def test_code_postal_invalid(self, lead):
        data = {
            "code_postal": "7A000",
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "code_postal" in serializer.errors

    def test_adresse_min_length(self, lead):
        data = {
            "adresse": "A",
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "adresse" in serializer.errors

    def test_ville_min_length(self, lead):
        data = {
            "ville": "A",
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "ville" in serializer.errors

    def test_remarques_max_length(self, lead):
        data = {
            "remarques": "a" * 300,
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "remarques" in serializer.errors

    def test_a_un_visa_sans_type(self, lead):
        data = {
            "a_un_visa": True,
            "type_visa": "",
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "type_visa" in serializer.errors

    def test_domaine_activite_obligatoire_si_situation(self, lead):
        data = {
            "situation_pro": "CDI",
            "domaine_activite": "",
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "domaine_activite" in serializer.errors

    def test_nombre_enfants_negative(self, lead):
        data = {
            "nombre_enfants": -1,
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "nombre_enfants" in serializer.errors

    def test_nombre_fiches_paie_negative(self, lead):
        data = {
            "nombre_fiches_paie": -3,
            "lead": lead.id,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "nombre_fiches_paie" in serializer.errors