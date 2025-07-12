import pytest
from api.lead_status.models import LeadStatus
from api.leads.models import Lead
from api.services.models import Service
from api.users.models import User

@pytest.fixture
def lead_status(db):
    return LeadStatus.objects.create(code="NOUVEAU", label="Nouveau", color="#000")

@pytest.fixture
def lead(db, lead_status):
    return Lead.objects.create(
        first_name="Jean", last_name="Dupont", status=lead_status
    )

@pytest.fixture
def service(db):
    return Service.objects.create(code="NATURALISATION", label="Naturalisation", price=300)

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@ex.com", password="User123!",
        first_name="Test", last_name="User",
        is_staff=False, is_superuser=False
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()