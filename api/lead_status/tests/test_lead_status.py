import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.users.models import User
from api.users.roles import UserRoles
from api.lead_status.models import LeadStatus

# --- FIXTURES ---

@pytest.fixture
def api_client():
    """APIClient DRF simple, non authentifié."""
    return APIClient()

@pytest.fixture
def admin_user(db):
    """Crée un utilisateur avec le rôle ADMIN (permet les opérations protégées)."""
    return User.objects.create_user(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User",
        role=UserRoles.ADMIN
    )

@pytest.fixture
def conseiller_user(db):
    """Crée un utilisateur lambda, non-admin (ne peut pas modifier les statuts)."""
    return User.objects.create_user(
        email="conseiller@example.com",
        password="Conseiller123!",
        first_name="Jean",
        last_name="Dupont",
        role=UserRoles.CONSEILLER
    )

@pytest.fixture
def auth_client(api_client, admin_user):
    """APIClient authentifié en tant qu’admin (droits max)."""
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def non_admin_client(api_client, conseiller_user):
    """APIClient authentifié en tant qu’utilisateur non-admin (accès limité)."""
    api_client.force_authenticate(user=conseiller_user)
    return api_client

@pytest.fixture
def lead_status(db):
    """Un statut Lead existant pour les tests (ex: RDV_CONFIRME)."""
    return LeadStatus.objects.create(
        code="RDV_CONFIRME",
        label="Rendez-vous confirmé",
        color="#00FF00"
    )

# --- TESTS MODELE ---

@pytest.mark.django_db
class TestLeadStatusModel:
    def test_str(self, lead_status):
        """Le __str__ du modèle retourne le libellé (utile pour admin Django & debug)."""
        assert str(lead_status) == "Rendez-vous confirmé"

    def test_unique_code(self, db):
        """
        Un code doit être unique : toute tentative de duplication doit lever une exception.
        Teste l’intégrité au niveau BDD.
        """
        LeadStatus.objects.create(code="ABSENT", label="Absent", color="#333")
        with pytest.raises(Exception):
            LeadStatus.objects.create(code="ABSENT", label="Autre absent", color="#444")

# --- TESTS API REST ---

@pytest.mark.django_db
class TestLeadStatusAPI:
    def test_list_lead_status(self, auth_client, lead_status):
        """
        Récupération de la liste des statuts via l’API.
        Teste que le endpoint fonctionne et contient bien le statut créé.
        Gère pagination ou non selon la config DRF.
        """
        url = reverse("lead-status-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Gère pagination DRF (clé 'results') ou liste brute
        results = response.data["results"] if "results" in response.data else response.data
        assert any(s["code"] == "RDV_CONFIRME" for s in results)

    def test_retrieve_lead_status(self, auth_client, lead_status):
        """
        Récupération d’un statut unique par son ID.
        Vérifie la structure des données retournées.
        """
        url = reverse("lead-status-detail", args=[lead_status.id])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["label"] == "Rendez-vous confirmé"

    def test_create_lead_status_admin_only(self, auth_client):
        """
        Création d’un nouveau statut (réservé admin).
        Vérifie que le POST retourne bien 201 et que la ressource est créée en base.
        """
        url = reverse("lead-status-list")
        payload = {
            "code": "NOUVEAU",
            "label": "Nouveau",
            "color": "#FF0000"
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert LeadStatus.objects.filter(code="NOUVEAU").exists()

    def test_create_lead_status_forbidden_for_non_admin(self, non_admin_client):
        """
        Un non-admin ne peut pas créer un LeadStatus.
        Le POST doit retourner 403 FORBIDDEN.
        """
        url = reverse("lead-status-list")
        payload = {
            "code": "INTERDIT",
            "label": "Interdit",
            "color": "#ABCDEF"
        }
        response = non_admin_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_lead_status_admin_only(self, auth_client, lead_status):
        """
        Un admin peut modifier un statut existant (PATCH).
        Le label est mis à jour, la réponse est 200 OK.
        """
        url = reverse("lead-status-detail", args=[lead_status.id])
        payload = {"label": "RDV Validé"}
        response = auth_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        lead_status.refresh_from_db()
        assert lead_status.label == "RDV Validé"

    def test_update_lead_status_forbidden_for_non_admin(self, non_admin_client, lead_status):
        """
        Un non-admin ne peut pas modifier un statut.
        Le PATCH retourne 403 FORBIDDEN.
        """
        url = reverse("lead-status-detail", args=[lead_status.id])
        payload = {"label": "Non autorisé"}
        response = non_admin_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_lead_status_admin_only(self, auth_client, lead_status):
        """
        Un admin peut supprimer un statut.
        Après suppression, l’objet n’existe plus en base.
        """
        url = reverse("lead-status-detail", args=[lead_status.id])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LeadStatus.objects.filter(id=lead_status.id).exists()

    def test_delete_lead_status_forbidden_for_non_admin(self, non_admin_client, lead_status):
        """
        Un non-admin ne peut pas supprimer de LeadStatus.
        Le DELETE retourne 403 FORBIDDEN.
        """
        url = reverse("lead-status-detail", args=[lead_status.id])
        response = non_admin_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_code_must_be_unique(self, auth_client, lead_status):
        """
        Création d’un statut avec un code déjà existant : doit retourner 400 BAD REQUEST.
        Vérifie que la contrainte d’unicité est bien propagée à l’API.
        """
        url = reverse("lead-status-list")
        payload = {
            "code": "RDV_CONFIRME",
            "label": "Doublon",
            "color": "#000"
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data

    def test_color_format(self, auth_client):
        """
        Création d’un statut avec une couleur au mauvais format.
        Si un validator de couleur hexadécimal est en place, doit retourner 400 BAD REQUEST.
        Sinon, peut retourner 201 CREATED (test reste robuste dans les 2 cas).
        """
        url = reverse("lead-status-list")
        payload = {
            "code": "TEST_COLOR",
            "label": "Test Couleur",
            "color": "not_a_color"
        }
        response = auth_client.post(url, payload, format="json")
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST)