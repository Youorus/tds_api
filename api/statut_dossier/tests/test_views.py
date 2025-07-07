import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.statut_dossiers.models import StatutDossier

@pytest.mark.django_db
def test_statut_dossier_list_authenticated():
    user = get_user_model().objects.create_user(email="a@a.fr", first_name="A", last_name="B", password="12345678")
    StatutDossier.objects.create(code="INCOMPLET", label="Incomplet", color="#333")
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/statut-dossiers/")
    assert resp.status_code == 200
    assert len(resp.data) >= 1

@pytest.mark.django_db
def test_statut_dossier_create():
    user = get_user_model().objects.create_user(email="a@a.fr", first_name="A", last_name="B", password="12345678")
    client = APIClient()
    client.force_authenticate(user=user)
    data = {"code": "TEST", "label": "Test", "color": "#000000"}
    resp = client.post("/api/statut-dossiers/", data)
    assert resp.status_code == 201
    assert resp.data["label"] == "Test"