import pytest
from rest_framework.test import APIClient
from decimal import Decimal
from api.users.roles import UserRoles

@pytest.mark.django_db
def test_create_contract_authenticated(user_admin, client, service):
    api_client = APIClient()
    api_client.force_authenticate(user=user_admin)
    payload = {
        "client": client.id,
        "service": service.id,
        "amount_due": "100.00",
        "discount_percent": "0.00",
    }
    response = api_client.post("/api/contracts/", payload)
    assert response.status_code == 201
    data = response.json()
    assert data["amount_due"] == "100.00"
    assert data["is_signed"] is False

@pytest.mark.django_db
def test_contract_list_requires_authentication():
    api_client = APIClient()
    response = api_client.get("/api/contracts/")
    assert response.status_code == 401  # Non authentifié

@pytest.mark.django_db
def test_contract_detail_view(user_admin, contract):
    api_client = APIClient()
    api_client.force_authenticate(user=user_admin)
    response = api_client.get(f"/api/contracts/{contract.id}/")
    assert response.status_code == 200
    assert response.data["id"] == contract.id

@pytest.mark.django_db
def test_contract_update_permission_denied(client, service, django_user_model):
    user = django_user_model.objects.create_user(email="accueil@x.com", password="pw", role=UserRoles.ACCUEIL)
    from api.contracts.models import Contract
    contract = Contract.objects.create(client=client, service=service, amount_due=Decimal("150.00"))
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    response = api_client.patch(f"/api/contracts/{contract.id}/", {"amount_due": "200.00"})
    assert response.status_code == 403
