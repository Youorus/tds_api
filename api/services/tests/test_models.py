import pytest
from decimal import Decimal
from api.services.models import Service

@pytest.mark.django_db
def test_service_creation():
    """
    Vérifie la création d'un service avec tous les champs requis.
    """
    service = Service.objects.create(
        code="NATURALISATION",
        label="Naturalisation",
        price=Decimal("200.00")
    )
    assert service.code == "NATURALISATION"
    assert service.label == "Naturalisation"
    assert service.price == Decimal("200.00")
    assert str(service) == "Naturalisation (200.00 €)"

@pytest.mark.django_db
def test_service_default_price():
    """
    Vérifie que le prix par défaut est bien 0.00 si non spécifié.
    """
    service = Service.objects.create(
        code="TITRE_SEJOUR",
        label="Titre de séjour"
    )
    assert service.price == Decimal("0.00")

@pytest.mark.django_db
def test_service_code_uniqueness():
    """
    Vérifie que la contrainte d'unicité du code fonctionne.
    """
    Service.objects.create(code="UNIQUE", label="Service A")
    with pytest.raises(Exception):
        Service.objects.create(code="UNIQUE", label="Service B")