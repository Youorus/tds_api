import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.payments.models import PaymentReceipt
from api.clients.models import Client
from api.contracts.models import Contract
from api.services.models import Service
from api.users.models import User, UserRoles
from api.lead_status.models import LeadStatus
from api.leads.models import Lead

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@ex.com", first_name="Admin", last_name="User", password="pwd", role=UserRoles.ADMIN)

@pytest.fixture
def client_user(db):
    return User.objects.create_user(email="user@ex.com", first_name="Jean", last_name="Dupont", password="pwd", role=UserRoles.CONSEILLER)

@pytest.fixture
def lead_status(db):
    return LeadStatus.objects.create(code="NOUVEAU", label="Nouveau")

@pytest.fixture
def client(client_user, lead_status):
    lead = Lead.objects.create(first_name="Jean", last_name="Dupont", status=lead_status)
    return Client.objects.create(lead=lead)

@pytest.fixture
def service(db):
    return Service.objects.create(code="SERVICE_TEST", label="Test Service", price=100)

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
class TestPaymentReceiptAPI:
    def test_create_receipt(self, admin_user, client, contract, monkeypatch):
        # Patch la fonction PDF pour les tests
        monkeypatch.setattr("api.payments.models.PaymentReceipt.generate_pdf", lambda self: None)
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("receipt-list")
        payload = {
            "client": client.id,
            "contract": contract.id,
            "amount": "150.00",
            "mode": "CB"
        }
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == 201

    def test_create_receipt_amount_zero_forbidden(self, admin_user, client, contract):
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("receipt-list")
        payload = {
            "client": client.id,
            "contract": contract.id,
            "amount": "0.00",
            "mode": "CB"
        }
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == 400

    def test_destroy_receipt(self, admin_user, client, contract):
        receipt = PaymentReceipt.objects.create(
            client=client,
            contract=contract,
            amount=100,
            mode="CB",
            created_by=admin_user
        )
        api_client = APIClient()
        api_client.force_authenticate(user=admin_user)
        url = reverse("receipt-detail", args=[receipt.id])
        resp = api_client.delete(url)
        assert resp.status_code == 204