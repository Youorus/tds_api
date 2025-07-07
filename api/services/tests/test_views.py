import pytest
from rest_framework.test import APIClient
from decimal import Decimal
from api.services.models import Service

@pytest.mark.django_db
def test_service_list_api():
    """
    Vérifie que la liste des services est exposée publiquement.
    """
    Service.objects.create(code="CODE1", label="Label1", price=10)
    Service.objects.create(code="CODE2", label="Label2", price=20)
    client = APIClient()
    response = client.get("/services/")
    assert response.status_code == 200
    assert len(response.data) == 2

@pytest.mark.django_db
def test_service_create_api():
    """
    Vérifie la création d’un service via l’API.
    """
    client = APIClient()
    data = {
        "code": "nouveau service",
        "label": "Nouveau Service",
        "price": "99.99"
    }
    response = client.post("/services/", data)
    assert response.status_code == 201
    assert response.data["code"] == "NOUVEAU_SERVICE"
    assert response.data["label"] == "Nouveau Service"
    assert response.data["price"] == "99.99"

@pytest.mark.django_db
def test_service_detail_api():
    """
    Vérifie le détail d'un service via l’API.
    """
    service = Service.objects.create(code="TEST_DETAIL", label="Detail", price=55)
    client = APIClient()
    response = client.get(f"/services/{service.id}/")
    assert response.status_code == 200
    assert response.data["label"] == "Detail"

@pytest.mark.django_db
def test_service_update_api():
    """
    Vérifie la modification d’un service via l’API.
    """
    service = Service.objects.create(code="UPDATE_ME", label="ToUpdate", price=5)
    client = APIClient()
    data = {
        "label": "Updated",
        "price": "10.00",
        "code": "update_me"
    }
    response = client.put(f"/services/{service.id}/", data)
    assert response.status_code == 200
    assert response.data["label"] == "Updated"
    assert response.data["price"] == "10.00"
    assert response.data["code"] == "UPDATE_ME"

@pytest.mark.django_db
def test_service_delete_api():
    """
    Vérifie la suppression d’un service via l’API.
    """
    service = Service.objects.create(code="TO_DELETE", label="DeleteMe", price=9)
    client = APIClient()
    response = client.delete(f"/services/{service.id}/")
    assert response.status_code == 204
    assert Service.objects.filter(id=service.id).count() == 0