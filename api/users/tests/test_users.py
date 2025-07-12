import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.users.models import User
from api.users.roles import UserRoles

# --- FIXTURES ---

@pytest.fixture
def api_client():
    """APIClient DRF simple, non authentifié."""
    return APIClient()

@pytest.fixture
def admin_user(db):
    """
    Crée un superutilisateur (admin) pour tester tous les endpoints protégés.
    Utilise la méthode create_superuser (règle métier : staff, superuser, admin).
    """
    return User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User"
    )

@pytest.fixture
def conseiller_user(db):
    """
    Crée un utilisateur lambda (conseiller).
    Sert à tester les permissions (ne doit rien pouvoir faire en dehors de la lecture de ses propres infos).
    """
    return User.objects.create_user(
        email="conseiller@example.com",
        password="Conseiller123!",
        first_name="Jean",
        last_name="Dupont"
    )

@pytest.fixture
def auth_client(api_client, admin_user):
    """
    APIClient authentifié en tant qu'admin pour simuler un appel avec droits maximum.
    """
    api_client.force_authenticate(user=admin_user)
    return api_client

# --- TESTS USER API ---

@pytest.mark.django_db
class TestUserViewSet:

    def test_admin_can_create_user(self, auth_client):
        """
        Cas standard : création d’un utilisateur par l’admin (POST).
        Teste la route, la réponse 201, l’enregistrement et la sécurité du mot de passe.
        """
        url = reverse("user-list")
        payload = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
            "role": UserRoles.CONSEILLER,
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="newuser@example.com")
        assert user.first_name == "New"
        # Le mot de passe est hashé en base (pas stocké en clair)
        assert user.check_password("StrongPass123!")
        assert user.role == UserRoles.CONSEILLER

    def test_create_user_without_password(self, auth_client):
        """
        Tentative de création sans mot de passe : la validation doit échouer.
        Cas classique de robustesse métier.
        """
        url = reverse("user-list")
        payload = {
            "email": "nopass@example.com",
            "first_name": "No",
            "last_name": "Pass",
            "role": UserRoles.ADMIN,
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_retrieve_user(self, auth_client, conseiller_user):
        """
        Récupération des infos d’un utilisateur existant (GET detail).
        Vérifie que l’API retourne les bonnes données.
        """
        url = reverse("user-detail", args=[conseiller_user.id])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == conseiller_user.email

    def test_update_user(self, auth_client, conseiller_user):
        """
        Modification partielle d’un utilisateur (PATCH).
        Vérifie que les modifications sont bien enregistrées.
        """
        url = reverse("user-detail", args=[conseiller_user.id])
        payload = {"first_name": "Jean-Michel"}
        response = auth_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        conseiller_user.refresh_from_db()
        assert conseiller_user.first_name == "Jean-Michel"

    def test_toggle_active(self, auth_client, conseiller_user):
        """
        Active puis désactive un utilisateur via l’endpoint custom.
        Vérifie les deux cas (False puis True) et l’état en base.
        """
        url = reverse("user-toggle-active", args=[conseiller_user.id])
        # Désactivation
        response = auth_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_200_OK
        conseiller_user.refresh_from_db()
        assert not conseiller_user.is_active
        # Réactivation
        response = auth_client.patch(url, {"is_active": True}, format="json")
        assert response.status_code == status.HTTP_200_OK
        conseiller_user.refresh_from_db()
        assert conseiller_user.is_active

    def test_toggle_active_requires_field(self, auth_client, conseiller_user):
        """
        La clé 'is_active' est obligatoire.
        Vérifie la robustesse métier de l’API (erreur claire si oubliée).
        """
        url = reverse("user-toggle-active", args=[conseiller_user.id])
        response = auth_client.patch(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "is_active" in response.data

    def test_change_password(self, auth_client, conseiller_user):
        """
        Changement de mot de passe par l’admin.
        Vérifie la mise à jour effective, la sécurité et la réponse.
        """
        url = reverse("user-change-password", args=[conseiller_user.id])
        response = auth_client.patch(url, {"new_password": "NouvelMdp2024!"})
        assert response.status_code == status.HTTP_200_OK
        conseiller_user.refresh_from_db()
        assert conseiller_user.check_password("NouvelMdp2024!")

    def test_change_password_same_as_current(self, auth_client, conseiller_user):
        """
        Refus si on tente de remettre le même mot de passe qu’actuel (bonne UX/sécurité).
        """
        url = reverse("user-change-password", args=[conseiller_user.id])
        response = auth_client.patch(url, {"new_password": "Conseiller123!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

    def test_change_password_validation(self, auth_client, conseiller_user):
        """
        Validation des règles sur le mot de passe : ici, il doit faire au moins 8 caractères.
        """
        url = reverse("user-change-password", args=[conseiller_user.id])
        response = auth_client.patch(url, {"new_password": "short"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

    def test_list_users(self, auth_client, conseiller_user):
        """
        Récupère la liste complète des users.
        Vérifie la présence d’un user spécifique dans la liste.
        """
        url = reverse("user-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Gestion pagination ou non
        results = response.data["results"] if "results" in response.data else response.data
        assert any(user["email"] == conseiller_user.email for user in results)

    def test_delete_user(self, auth_client, conseiller_user):
        """
        Suppression d’un utilisateur.
        Vérifie la réponse API et l’état en base.
        """
        url = reverse("user-detail", args=[conseiller_user.id])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=conseiller_user.id).exists()

    def test_permissions_forbidden_for_non_admin(self, api_client, conseiller_user):
        """
        Un utilisateur lambda ne peut pas accéder à la liste des users (403 attendu).
        Vérifie la robustesse des permissions backend.
        """
        api_client.force_authenticate(user=conseiller_user)
        url = reverse("user-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_set_superuser_fields(self, auth_client):
        """
        Un admin qui tente de créer un user en forçant is_staff ou is_superuser à True
        ne doit pas pouvoir bypasser les règles du modèle (sauf rôle ADMIN).
        Ce test protège contre les attaques via l’API.
        """
        url = reverse("user-list")
        payload = {
            "email": "malicious@example.com",
            "first_name": "Mal",
            "last_name": "User",
            "password": "Malicious123!",
            "role": UserRoles.CONSEILLER,
            "is_staff": True,
            "is_superuser": True
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="malicious@example.com")
        # Doit être admin pour être superuser (règle du modèle)
        assert not user.is_superuser or user.role == UserRoles.ADMIN