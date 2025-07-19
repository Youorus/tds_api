import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.services.models import Service
from api.users.models import User
from api.users.roles import UserRoles

# ---------- FIXTURES ----------

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    # Utilisateur staff/admin
    return User.objects.create_user(
        email="admin@ex.com",
        password="Admin123!",
        first_name="Admin",
        last_name="User",
        role=UserRoles.ADMIN,
        is_staff=True,
        is_superuser=False
    )

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@ex.com", password="User123!",
        is_staff=False,
        is_superuser=False,
        first_name="User", last_name="Test", role=UserRoles.CONSEILLER,
    )

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def user_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def service(db):
    return Service.objects.create(code="TITRESEJOUR", label="Titre de séjour", price="120.00")

# ---------- TESTS CRUD & LOGIQUE ----------

@pytest.mark.django_db
class TestServiceAPI:

    def test_non_admin_cannot_create_service(self, user_client):
        url = reverse("services-list")
        payload = {"code": "TEST", "label": "Essai", "price": "50"}
        resp = user_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert not Service.objects.filter(label="Essai").exists()
        assert "detail" in resp.data  # Vérifie qu'un message d'erreur est présent

    def test_non_admin_cannot_update_service(self, user_client, service):
        url = reverse("services-detail", args=[service.id])
        resp = user_client.patch(url, {"price": "80.00"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        service.refresh_from_db()
        assert str(service.price) == "120.00"

    def test_non_admin_cannot_delete_service(self, user_client, service):
        url = reverse("services-detail", args=[service.id])
        resp = user_client.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert Service.objects.filter(id=service.id).exists()

    def test_admin_can_update_service(self, admin_client, service):
        url = reverse("services-detail", args=[service.id])
        resp = admin_client.patch(url, {"price": "150.00"}, format="json")
        assert resp.status_code == 200
        service.refresh_from_db()
        assert str(service.price) == "150.00"

    def test_admin_can_delete_service(self, admin_client, service):
        url = reverse("services-detail", args=[service.id])
        resp = admin_client.delete(url)
        assert resp.status_code == 204
        assert not Service.objects.filter(id=service.id).exists()

    def test_label_min_length_validation(self, admin_client):
        url = reverse("services-list")
        payload = {"code": "TST", "label": "Ab", "price": "30"}
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == 400
        assert "label" in resp.data

    def test_price_cannot_be_negative(self, admin_client):
        url = reverse("services-list")
        payload = {"code": "TST", "label": "Negatif", "price": "-10"}
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == 400
        assert "price" in resp.data

    def test_service_code_is_always_normalized_on_save(self, admin_client):
        url = reverse("services-list")
        payload = {"code": " titre - séjour  ", "label": "Nettoye", "price": "77"}
        resp = admin_client.post(url, payload, format="json")
        assert resp.status_code == 201
        service = Service.objects.get(label="Nettoye")
        assert service.code == "TITRESEJOUR"

    def test_list_services_public(self, api_client, service):
        url = reverse("services-list")
        resp = api_client.get(url)
        assert resp.status_code == 200
        # Pagination DRF ou pas
        if isinstance(resp.data, dict) and 'results' in resp.data:
            data = resp.data['results']
        else:
            data = resp.data
        labels = [item["label"] for item in data]
        assert "Titre de séjour" in labels

    def test_unauthenticated_user_cannot_create_service(self, api_client):
        url = reverse("services-list")
        payload = {"code": "TST", "label": "Test non auth", "price": "15"}
        resp = api_client.post(url, payload, format="json")
        # Non authentifié : 401
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED