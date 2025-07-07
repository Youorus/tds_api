import pytest
from decimal import Decimal
from api.services.serializers import ServiceSerializer
from api.services.models import Service

@pytest.mark.django_db
def test_valid_service_serializer():
    """
    Vérifie que la sérialisation d'un service fonctionne.
    """
    data = {
        "code": "TITRE_SEJOUR",
        "label": "Titre de séjour",
        "price": "350.50"
    }
    serializer = ServiceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.code == "TITRE_SEJOUR"
    assert instance.label == "Titre de séjour"
    assert instance.price == Decimal("350.50")

@pytest.mark.django_db
def test_serializer_code_formatting():
    """
    Le code doit être transformé en MAJUSCULES et avec underscore.
    """
    data = {
        "code": "titre séjour",
        "label": "Titre séjour",
        "price": "123.45"
    }
    serializer = ServiceSerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()
    assert instance.code == "TITRE_SÉJOUR"

@pytest.mark.django_db
def test_serializer_label_too_short():
    """
    Le label trop court doit être rejeté.
    """
    data = {
        "code": "COURT",
        "label": "AB",
        "price": "100"
    }
    serializer = ServiceSerializer(data=data)
    assert not serializer.is_valid()
    assert "label" in serializer.errors

@pytest.mark.django_db
def test_serializer_negative_price():
    """
    Le prix négatif doit être refusé.
    """
    data = {
        "code": "NEGATIF",
        "label": "Service Test",
        "price": "-1"
    }
    serializer = ServiceSerializer(data=data)
    assert not serializer.is_valid()
    assert "price" in serializer.errors