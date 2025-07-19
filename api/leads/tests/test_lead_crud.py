# api/leads/tests/test_lead_crud.py

import pytest
from django.urls import reverse
from rest_framework import status
from api.users.models import User
from api.users.roles import UserRoles
from api.lead_status.models import LeadStatus
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
def accueil_user(db):
    return User.objects.create_user(
        email="accueil@ex.com", password="Accueil123!",
        first_name="Accueil", last_name="User", role=UserRoles.ACCUEIL
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
def accueil_client(accueil_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=accueil_user)
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
def public_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def status_rdv_planifie(db):
    return LeadStatus.objects.create(code="RDV_PLANIFIE", label="RDV planifié", color="#ffcc00")

@pytest.fixture
def lead(admin_user, status_rdv_planifie):
    return Lead.objects.create(
        first_name="Alice", last_name="Test", phone="+33611112222", email="alice@test.com",
        status=status_rdv_planifie, assigned_to=admin_user, appointment_date=aware_datetime(2031, 1, 1, 10, 0),
    )

@pytest.mark.django_db
class TestLeadCRUD:

    def test_admin_can_create_lead(self, admin_client, status_rdv_planifie):
        url = reverse("leads-list")
        payload = {
            "first_name": "Bob", "last_name": "Martin", "phone": "+33612345678",
            "email": "bob@example.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "22/12/2030 10:00"
        }
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Lead.objects.filter(email="bob@example.com").exists()

    def test_accueil_can_create_lead(self, accueil_client, status_rdv_planifie):
        url = reverse("leads-list")
        payload = {
            "first_name": "Accueil", "last_name": "User", "phone": "+33633334444",
            "email": "accueil@lead.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "23/12/2030 11:00"
        }
        resp = accueil_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_conseiller_cannot_create_lead(self, conseiller_client, status_rdv_planifie):
        url = reverse("leads-list")
        payload = {
            "first_name": "Conseiller", "last_name": "Lead", "phone": "+33698765432",
            "email": "conseiller@lead.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "24/12/2030 12:00"
        }
        resp = conseiller_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_juriste_cannot_create_lead(self, juriste_client, status_rdv_planifie):
        url = reverse("leads-list")
        payload = {
            "first_name": "Jules", "last_name": "Legal", "phone": "+33622223333",
            "email": "juriste@lead.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "25/12/2030 09:00"
        }
        resp = juriste_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_public_create_lead_open_to_everyone(self, public_client, status_rdv_planifie):
        url = reverse("leads-public-create")
        payload = {
            "first_name": "Public", "last_name": "Test", "phone": "+33699887766",
            "email": "public@open.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "26/12/2030 15:00"
        }
        resp = public_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Lead.objects.filter(email="public@open.com").exists()

    def test_lead_update_possible_by_anyone(self, admin_client, lead):
        url = reverse("leads-detail", args=[lead.id])
        resp = admin_client.patch(url, {"phone": "+33777777777"}, format="json")
        assert resp.status_code == 200
        lead.refresh_from_db()
        assert lead.phone == "+33777777777"

    def test_lead_delete_possible_by_anyone(self, accueil_client, lead):
        url = reverse("leads-detail", args=[lead.id])
        resp = accueil_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Lead.objects.filter(id=lead.id).exists()

    def test_lead_retrieve_possible_by_anyone(self, juriste_client, lead):
        url = reverse("leads-detail", args=[lead.id])
        resp = juriste_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == lead.email

    def test_unique_phone_on_create(self, admin_client, status_rdv_planifie):
        Lead.objects.create(
            first_name="Dup", last_name="User", phone="+33645454545",
            status=status_rdv_planifie,
            appointment_date=aware_datetime(2030, 12, 31, 10, 0)
        )
        url = reverse("leads-list")
        payload = {
            "first_name": "Dup2", "last_name": "User", "phone": "+33645454545",
            "email": "dup2@dup.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "01/01/2031 10:00"
        }
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in resp.data

    def test_unique_email_on_create(self, admin_client, status_rdv_planifie):
        Lead.objects.create(
            first_name="Dup", last_name="User", phone="+33600000000", email="mail@dup.com",
            status=status_rdv_planifie,
            appointment_date=aware_datetime(2031, 1, 1, 10, 0)
        )
        url = reverse("leads-list")
        payload = {
            "first_name": "Dup2", "last_name": "User", "phone": "+33610000001",
            "email": "mail@dup.com", "status_id": status_rdv_planifie.id,
            "appointment_date": "01/01/2031 10:00"
        }
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in resp.data