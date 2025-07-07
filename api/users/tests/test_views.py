import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from api.users.models import User
from api.users.roles import UserRoles


@pytest.mark.django_db
class TestUserViewSet:
    """
    Tests d'intégration pour la vue UserViewSet.
    Couvre toutes les opérations CRUD et actions personnalisées.
    """

    def setup_method(self):
        # Crée et connecte un superuser pour tous les tests
        self.admin = User.objects.create_superuser(
            email="admin@ex.com",
            first_name="Super",
            last_name="Admin",
            password="Admin@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_list_users(self):
        """
        Teste la récupération de la liste des utilisateurs.
        """
        User.objects.create_user(
            email="user1@ex.com", first_name="U1", last_name="Test", password="pass123"
        )
        url = reverse("user-list")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert isinstance(resp.data, list) or isinstance(resp.data, dict)  # Selon pagination

    def test_retrieve_user(self):
        """
        Teste la récupération du détail d'un utilisateur.
        """
        user = User.objects.create_user(
            email="find@ex.com", first_name="Find", last_name="Me", password="Find@123"
        )
        url = reverse("user-detail", args=[user.pk])
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data["email"] == "find@ex.com"

    def test_create_user(self):
        """
        Teste la création d'un nouvel utilisateur.
        """
        url = reverse("user-list")
        data = {
            "email": "newuser@ex.com",
            "first_name": "New",
            "last_name": "User",
            "password": "User@12345",
            "role": UserRoles.CONSEILLER,
        }
        resp = self.client.post(url, data)
        assert resp.status_code == 201
        assert User.objects.filter(email="newuser@ex.com").exists()

    def test_update_user(self):
        """
        Teste la mise à jour partielle d'un utilisateur existant.
        """
        user = User.objects.create_user(
            email="edit@ex.com", first_name="Edit", last_name="Me", password="Edit@123"
        )
        url = reverse("user-detail", args=[user.pk])
        data = {"first_name": "Edited"}
        resp = self.client.patch(url, data)
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Edited"

    def test_delete_user(self):
        """
        Teste la suppression d'un utilisateur.
        """
        user = User.objects.create_user(
            email="del@ex.com", first_name="Delete", last_name="Me", password="Del@123"
        )
        url = reverse("user-detail", args=[user.pk])
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not User.objects.filter(email="del@ex.com").exists()

    def test_toggle_active_action(self):
        """
        Teste l'action personnalisée de (dés)activation d'utilisateur.
        """
        user = User.objects.create_user(
            email="act@ex.com", first_name="Active", last_name="One", password="Act@123"
        )
        url = reverse("user-toggle-active", args=[user.pk])
        resp = self.client.patch(url, {"is_active": False})
        assert resp.status_code == 200
        user.refresh_from_db()
        assert not user.is_active

    def test_change_password_action(self):
        """
        Teste l'action personnalisée de changement de mot de passe.
        """
        user = User.objects.create_user(
            email="pass@ex.com", first_name="Pass", last_name="Word", password="Old@123"
        )
        url = reverse("user-change-password", args=[user.pk])
        resp = self.client.patch(url, {"new_password": "New@12345"})
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("New@12345")