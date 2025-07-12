import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.contracts.models import Contract
from api.clients.models import Client
from api.services.models import Service
from api.users.models import User, UserRoles
from api.lead_status.models import LeadStatus

@pytest.fixture
def lead_status(db):
    return LeadStatus.objects.create(code="NOUVEAU", label="Nouveau", color="#C1E8FF")

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@ex.com", first_name="Admin", last_name="User",
        password="pwd", role=UserRoles.ADMIN
    )

@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        email="user@ex.com", first_name="Jean", last_name="Dupont",
        password="pwd", role=UserRoles.CONSEILLER
    )

@pytest.fixture
def client(client_user, lead_status):
    from api.leads.models import Lead
    lead = Lead.objects.create(first_name="Jean", last_name="Dupont", status=lead_status)
    return Client.objects.create(lead=lead)

@pytest.fixture
def service(db):
    # Correction ici : pas de "name", mais "code" et "label"
    return Service.objects.create(
        code="SERVICE_TEST",
        label="Service test",
        price=100
    )

@pytest.fixture
def contract(client, admin_user, service):
    return Contract.objects.create(
        client=client,
        created_by=admin_user,
        service=service,
        amount_due=200,
        discount_percent=10
    )

@pytest.mark.django_db
class TestContractAPI:
    def test_list_contracts(self, admin_user):
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("contracts-list")
        resp = api_client.get(url)
        assert resp.status_code == 200

    def test_create_contract(self, admin_user, client, service):
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("contracts-list")
        payload = {
            "client": client.id,
            "service": service.id,
            "amount_due": "150.00",
            "discount_percent": "5.00",
        }
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == 201

    def test_update_contract_signed(self, contract, admin_user):
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("contracts-detail", args=[contract.id])
        resp = api_client.patch(url, {"is_signed": True}, format="json")
        assert resp.status_code == 200
        contract.refresh_from_db()
        assert contract.is_signed is True

    def test_delete_contract(self, contract, admin_user):
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("contracts-detail", args=[contract.id])
        resp = api_client.delete(url)
        assert resp.status_code == 204