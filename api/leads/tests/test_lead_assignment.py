# api/leads/tests/test_lead_assignment.py

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
def conseiller_user(db):
    return User.objects.create_user(
        email="conseiller@ex.com", password="Conseiller123!",
        first_name="Jean", last_name="Dupont", role=UserRoles.CONSEILLER
    )

@pytest.fixture
def juriste_user(db):
    return User.objects.create_user(
        email="juriste@ex.com", password="Juriste123!",
        first_name="Jules", last_name="Legal", role=UserRoles.JURISTE
    )

@pytest.fixture
def admin_client(admin_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client

@pytest.fixture
def conseiller_client(conseiller_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=conseiller_user)
    return client

@pytest.fixture
def juriste_client(juriste_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=juriste_user)
    return client

@pytest.fixture
def status_rdv_planifie(db):
    return LeadStatus.objects.create(code="RDV_PLANIFIE", label="RDV planifié", color="#ffcc00")

@pytest.fixture
def status_present(db):
    return LeadStatus.objects.create(code="PRESENT", label="Présent", color="#00ccff")

@pytest.fixture
def lead(admin_user, status_rdv_planifie):
    return Lead.objects.create(
        first_name="Alice", last_name="Test", phone="+33611112222", email="alice@test.com",
        status=status_rdv_planifie, assigned_to=admin_user, appointment_date=aware_datetime(2031, 1, 1, 10, 0),
    )

@pytest.mark.django_db
class TestLeadAssignment:

    def test_admin_can_assign_lead(self, admin_client, conseiller_user, lead):
        url = reverse("leads-assignment", args=[lead.id])
        resp = admin_client.patch(url, {"assigned_to": conseiller_user.id}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        lead.refresh_from_db()
        assert lead.assigned_to == conseiller_user

    def test_conseiller_can_self_assign_lead(self, conseiller_client, conseiller_user, lead, status_present):
        lead.assigned_to = None
        lead.status = status_present
        lead.save()
        url = reverse("leads-assignment", args=[lead.id])
        resp = conseiller_client.patch(url, {"assigned_to": conseiller_user.id}, format="json")
        assert resp.status_code == 200
        lead.refresh_from_db()
        assert lead.assigned_to == conseiller_user

    def test_conseiller_cannot_assign_other(self, conseiller_client, admin_user, lead, status_present):
        lead.assigned_to = None
        lead.status = status_present
        lead.save()
        url = reverse("leads-assignment", args=[lead.id])
        resp = conseiller_client.patch(url, {"assigned_to": admin_user.id}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_unassign_any_lead(self, admin_client, lead):
        url = reverse("leads-assignment", args=[lead.id])
        response = admin_client.patch(url, {"assigned_to": None}, format="json")
        assert response.status_code == 200
        lead.refresh_from_db()
        assert lead.assigned_to is None

    def test_juriste_cannot_assign_or_unassign(self, juriste_client, juriste_user, lead):
        url = reverse("leads-assignment", args=[lead.id])
        resp = juriste_client.patch(url, {"assigned_to": juriste_user.id}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN