import pytest
from decimal import Decimal
from django.utils import timezone
from api.contracts.models import Contract
from api.clients.models import Client
from api.users.models import User
from api.services.models import Service

@pytest.mark.django_db
def test_contract_creation(client, user_admin, service):
    contract = Contract.objects.create(
        client=client,
        created_by=user_admin,
        service=service,
        amount_due=Decimal("250.00"),
        discount_percent=Decimal("10.00"),
    )
    assert contract.client == client
    assert contract.created_by == user_admin
    assert contract.service == service
    assert contract.amount_due == Decimal("250.00")
    assert contract.discount_percent == Decimal("10.00")
    assert not contract.is_signed

@pytest.mark.django_db
def test_contract_real_amount_calculation(contract):
    # Suppose discount is 10%
    contract.discount_percent = Decimal("10.00")
    contract.amount_due = Decimal("100.00")
    contract.save()
    assert contract.real_amount == Decimal("90.00")

@pytest.mark.django_db
def test_contract_str_display(contract):
    assert str(contract).startswith(f"Contrat {contract.id} - {contract.client}")

# Fixtures utiles pour DRY (si besoin)
@pytest.fixture
def user_admin(db):
    from api.users.models import User
    return User.objects.create_user(email="admin@x.com", password="pw", role="ADMIN")

@pytest.fixture
def client(db, user_admin):
    from api.leads.models import Lead
    from api.clients.models import Client
    lead = Lead.objects.create(first_name="John", last_name="Doe", phone="+33123456789", status_id=1)
    return Client.objects.create(lead=lead)

@pytest.fixture
def service(db):
    from api.services.models import Service
    return Service.objects.create(code="TEST", label="Service Test", price=Decimal("50.00"))

@pytest.fixture
def contract(db, client, user_admin, service):
    return Contract.objects.create(client=client, created_by=user_admin, service=service, amount_due=Decimal("100.00"))