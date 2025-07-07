import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
def test_login_success_returns_tokens_and_user():
    """
    Vérifie qu’un utilisateur valide reçoit bien ses tokens et infos après login.
    """
    user = User.objects.create_user(
        email="user@example.com", first_name="Test", last_name="User", password="azerty123", role="ADMIN"
    )
    client = APIClient()
    url = reverse('login')
    response = client.post(url, {"email": "user@example.com", "password": "azerty123"}, format='json')
    assert response.status_code == 200
    data = response.json()
    assert "tokens" in data
    assert "access" in data["tokens"]
    assert "refresh" in data["tokens"]
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["role"] == "ADMIN"

@pytest.mark.django_db
def test_login_fails_on_wrong_password():
    """
    Vérifie qu’un mauvais mot de passe retourne une erreur.
    """
    User.objects.create_user(email="user@example.com", first_name="Test", last_name="User", password="azerty123")
    client = APIClient()
    url = reverse('login')
    response = client.post(url, {"email": "user@example.com", "password": "mauvais"}, format='json')
    assert response.status_code == 400
    assert "password" in response.json()

@pytest.mark.django_db
def test_login_fails_if_user_inactive():
    """
    Vérifie qu’un utilisateur désactivé ne peut pas se connecter.
    """
    user = User.objects.create_user(email="inactive@example.com", first_name="Inactif", last_name="User", password="azerty123", is_active=False)
    client = APIClient()
    url = reverse('login')
    response = client.post(url, {"email": "inactive@example.com", "password": "azerty123"}, format='json')
    assert response.status_code == 400
    assert "non_field_errors" in response.json()

@pytest.mark.django_db
def test_login_fails_if_user_does_not_exist():
    """
    Vérifie qu’un email inconnu retourne une erreur.
    """
    client = APIClient()
    url = reverse('login')
    response = client.post(url, {"email": "doesnotexist@example.com", "password": "pass"}, format='json')
    assert response.status_code == 400
    assert "email" in response.json()