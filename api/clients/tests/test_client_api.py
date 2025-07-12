import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from api.leads.models import Lead
from api.lead_status.models import LeadStatus
from api.statut_dossier.models import StatutDossier
from api.clients.models import Client

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="testpass123",
        first_name="Test",
        last_name="User"
    )

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
        color="#00AA00"
    )

@pytest.fixture
def lead(user, statut_dossier, lead_status):
    # Si Lead a un champ created_by ou user, ajoute-le ici.
    return Lead.objects.create(
        first_name="Marc",
        last_name="Nkue",
        phone="0601020304",
        email="marc@example.com",
        status=lead_status,
        statut_dossier=statut_dossier
    )

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestClientAPI:
    def test_create_client_public(self, api_client, lead):
        url = reverse("clients-list") + f"?id={lead.id}"
        payload = {
            "adresse": "1 rue de Paris",
            "ville": "Paris",
            "code_postal": "75000",
        }
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == 201
        assert Client.objects.filter(adresse="1 rue de Paris").exists()

    def test_create_client_duplicate_forbidden(self, api_client, lead):
        url = reverse("clients-list") + f"?id={lead.id}"
        payload = {"adresse": "2 avenue Paris"}
        api_client.post(url, payload, format="json")
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == 400

    def test_update_client_requires_auth(self, api_client, lead):
        url = reverse("clients-list") + f"?id={lead.id}"
        payload = {"adresse": "12 rue test"}
        create_resp = api_client.post(url, payload, format="json")
        assert create_resp.status_code == 201
        client_id = create_resp.data["id"]
        update_url = reverse("clients-detail", args=[client_id])
        resp = api_client.patch(update_url, {"adresse": "Nouvelle adresse"}, format="json")
        assert resp.status_code in (401, 403)  # Non authentifié, donc interdit

    def test_patch_partial_update(self, lead, user):
        url = reverse("clients-list") + f"?id={lead.id}"
        api_client = APIClient()
        payload = {"adresse": "9 place test"}
        create_resp = api_client.post(url, payload, format="json")
        assert create_resp.status_code == 201
        client_id = create_resp.data["id"]
        update_url = reverse("clients-detail", args=[client_id])

        # Authentifie un user pour le patch (ici ton lead.created_by)
        authenticated_client = APIClient()
        authenticated_client.force_authenticate(user=user)
        resp = authenticated_client.patch(update_url, {"ville": "Pontoise"}, format="json")
        assert resp.status_code == 200
        client = Client.objects.get(pk=client_id)
        assert client.ville == "Pontoise"