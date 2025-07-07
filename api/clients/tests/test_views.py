
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.leads.models import Lead
from api.clients.models import Client
from django.contrib.auth import get_user_model

from api.services.models import Service

pytestmark = pytest.mark.django_db

@pytest.fixture
def lead():
    return Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)

@pytest.fixture
def client_api():
    return APIClient()

@pytest.fixture
def service():
    return Service.objects.create(label="Naturalisation", code="NAT")

@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(email="user@test.com", first_name="User", last_name="Test", password="password")

@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

def get_client_list_url():
    return reverse("clients-list")  # basename de ton router : 'clients'

def get_client_detail_url(pk):
    return reverse("clients-detail", args=[pk])

def test_public_create_client_ok(client_api, lead, service):
    """
    Teste la création d’un client sans authentification (POST public).
    """
    data = {
        "adresse": "12 avenue Paris",
        "ville": "Paris",
        "code_postal": "75001",
        "type_demande_id": service.id,
        "date_naissance": "1995-12-01"
    }
    url = get_client_list_url() + f"?id={lead.id}"
    response = client_api.post(url, data)
    assert response.status_code == 201
    assert Client.objects.count() == 1
    c = Client.objects.first()
    assert c.lead == lead

def test_prevent_double_formulaire(client_api, lead, service):
    """
    On ne peut pas créer deux fois un formulaire pour le même lead.
    """
    Client.objects.create(
        lead=lead,
        adresse="1 rue",
        ville="Paris",
        code_postal="75001"
    )
    data = {
        "adresse": "1 rue",
        "ville": "Paris",
        "code_postal": "75001",
        "type_demande_id": service.id
    }
    url = get_client_list_url() + f"?id={lead.id}"
    response = client_api.post(url, data)
    assert response.status_code == 400
    assert "lead" in response.data

def test_create_client_without_lead_ok(auth_client, service):
    """
    Un utilisateur connecté peut créer un client sans lead (cas admin/backoffice).
    """
    data = {
        "adresse": "1 rue du back",
        "ville": "Paris",
        "code_postal": "75001",
        "type_demande_id": service.id
    }
    url = get_client_list_url()
    response = auth_client.post(url, data)
    assert response.status_code == 201
    assert Client.objects.count() == 1

def test_list_clients_requires_auth(client_api):
    """
    On ne peut PAS lister les clients sans authentification.
    """
    url = get_client_list_url()
    response = client_api.get(url)
    assert response.status_code in (401, 403)

def test_list_clients_authenticated(auth_client, lead, service):
    """
    Un utilisateur connecté peut lister les clients.
    """
    Client.objects.create(lead=lead, adresse="Rue", ville="P", code_postal="75001")
    url = get_client_list_url()
    response = auth_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) == 1

def test_update_client(auth_client, lead, service):
    """
    Un utilisateur connecté peut mettre à jour un client existant.
    """
    client = Client.objects.create(lead=lead, adresse="Rue", ville="Paris", code_postal="75001")
    url = get_client_detail_url(client.pk)
    data = {
        "adresse": "Nouvelle adresse",
        "ville": "Paris",
        "code_postal": "75001",
        "type_demande_id": service.id
    }
    response = auth_client.patch(url, data)
    assert response.status_code == 200
    client.refresh_from_db()
    assert client.adresse == "Nouvelle adresse"

def test_delete_client(auth_client, lead):
    """
    Un utilisateur connecté peut supprimer un client.
    """
    client = Client.objects.create(lead=lead, adresse="Rue", ville="Paris", code_postal="75001")
    url = get_client_detail_url(client.pk)
    response = auth_client.delete(url)
    assert response.status_code == 204
    assert Client.objects.count() == 0

def test_create_with_inexistant_lead(client_api, service):
    """
    Créer un client avec un ID de lead inexistant retourne une erreur.
    """
    data = {
        "adresse": "Rue bidon",
        "ville": "Paris",
        "code_postal": "75001",
        "type_demande_id": service.id
    }
    url = get_client_list_url() + "?id=99999"
    response = client_api.post(url, data)
    assert response.status_code == 400
    assert "lead" in response.data