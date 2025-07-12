import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    user = User.objects.create_user(
        email="test@ex.com", first_name="Marc", last_name="Nkue", password="azerty123", role="ADMIN"
    )
    user.is_active = True
    user.save()
    return user

@pytest.mark.django_db
class TestLoginAPI:
    def test_login_success(self, user):
        client = APIClient()
        url = reverse("login")
        payload = {
            "email": user.email,
            "password": "azerty123"
        }
        resp = client.post(url, payload, format="json")
        assert resp.status_code == 200
        assert "tokens" in resp.data
        assert "user" in resp.data
        assert resp.data["user"]["email"] == user.email

    def test_login_wrong_email(self):
        client = APIClient()
        url = reverse("login")
        payload = {
            "email": "notfound@ex.com",
            "password": "azerty123"
        }
        resp = client.post(url, payload, format="json")
        assert resp.status_code == 400
        assert "email" in resp.data

    def test_login_wrong_password(self, user):
        client = APIClient()
        url = reverse("login")
        payload = {
            "email": user.email,
            "password": "WRONG"
        }
        resp = client.post(url, payload, format="json")
        assert resp.status_code == 400
        assert "password" in resp.data

    def test_login_inactive_user(self, user):
        user.is_active = False
        user.save()
        client = APIClient()
        url = reverse("login")
        payload = {
            "email": user.email,
            "password": "azerty123"
        }
        resp = client.post(url, payload, format="json")
        assert resp.status_code == 400
        assert "non_field_errors" in resp.data