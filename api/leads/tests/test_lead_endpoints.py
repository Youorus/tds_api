# api/leads/tests/test_lead_endpoints.py

import pytest
from django.urls import reverse
from rest_framework import status
from api.lead_status.models import LeadStatus
from api.users.models import User
from api.users.roles import UserRoles
from api.leads.models import Lead

def aware_datetime(year, month, day, hour, minute):
    import datetime
    from django.utils import timezone
    return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@ex.com", password="Admin123!",
        first_name="Admin", last_name="User", role=UserRoles.ADMIN, is_staff=True
    )

@pytest.fixture
def admin_client(admin_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client

@pytest.fixture
def public_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def status_rdv_planifie(db):
    return LeadStatus.objects.create(code="RDV_PLANIFIE", label="RDV planifié", color="#ffcc00")

@pytest.fixture
def status_rdv_confirme(db):
    return LeadStatus.objects.create(code="RDV_CONFIRME", label="RDV confirmé", color="#00ff00")

@pytest.fixture
def lead(admin_user, status_rdv_planifie):
    return Lead.objects.create(
        first_name="Alice", last_name="Test", phone="+33611112222", email="alice@test.com",
        status=status_rdv_planifie, assigned_to=admin_user, appointment_date=aware_datetime(2031, 1, 1, 10, 0),
    )

@pytest.mark.django_db
class TestLeadEndpoints:

    def test_count_by_status_endpoint(self, admin_client, status_rdv_planifie, status_rdv_confirme):
        Lead.objects.create(first_name="Stat1", last_name="Toto", phone="+33612340001", status=status_rdv_planifie, appointment_date=aware_datetime(2031, 1, 1, 10, 0))
        Lead.objects.create(first_name="Stat2", last_name="Titi", phone="+33612340002", status=status_rdv_confirme, appointment_date=aware_datetime(2031, 1, 1, 10, 0))
        url = reverse("leads-count-by-status")
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert "RDV_PLANIFIE" in resp.data
        assert "RDV_CONFIRME" in resp.data

    def test_permissions_forbidden_for_non_authenticated(self, public_client, lead):
        url = reverse("leads-detail", args=[lead.id])
        resp = public_client.get(url)
        assert resp.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]