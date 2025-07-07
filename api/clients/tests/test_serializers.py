import pytest
from api.clients.serializers import ClientSerializer
from api.leads.models import Lead
from datetime import date, timedelta

from api.services.models import Service


@pytest.mark.django_db
def test_client_serializer_valid_minimal():
    """
    Teste la sérialisation avec uniquement le minimum requis (lead déjà existant).
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    data = {
        "adresse": "10 rue de Paris",
        "ville": "Paris",
        "code_postal": "75001",
    }
    serializer = ClientSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

@pytest.mark.django_db
def test_client_serializer_invalid_date_naissance():
    """
    Teste la validation de la date de naissance dans le futur (doit échouer).
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    data = {
        "adresse": "10 rue de Paris",
        "ville": "Paris",
        "code_postal": "75001",
        "date_naissance": (date.today() + timedelta(days=1)).isoformat()
    }
    serializer = ClientSerializer(data=data)
    assert not serializer.is_valid()
    assert "date_naissance" in serializer.errors

@pytest.mark.django_db
def test_client_serializer_code_postal_invalid():
    """
    Teste la validation du code postal non numérique ou trop court/long.
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    for bad_cp in ["1", "ABCDEF", "7500X", "123"]:
        data = {
            "adresse": "1 rue",
            "ville": "Paris",
            "code_postal": bad_cp,
        }
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "code_postal" in serializer.errors

@pytest.mark.django_db
def test_client_serializer_validate_negative_values():
    """
    Teste la validation sur les nombres négatifs (enfants, fiches de paie...).
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    data = {
        "adresse": "10 rue",
        "ville": "Paris",
        "code_postal": "75001",
        "nombre_enfants": -1,
        "nombre_enfants_francais": -1,
        "nombre_fiches_paie": -2,
    }
    serializer = ClientSerializer(data=data)
    assert not serializer.is_valid()
    assert "nombre_enfants" in serializer.errors
    assert "nombre_enfants_francais" in serializer.errors
    assert "nombre_fiches_paie" in serializer.errors

@pytest.mark.django_db
def test_client_serializer_remarques_trop_long():
    """
    Teste la validation du champ remarques trop long.
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    data = {
        "adresse": "10 rue",
        "ville": "Paris",
        "code_postal": "75001",
        "remarques": "A" * 256,
    }
    serializer = ClientSerializer(data=data)
    assert not serializer.is_valid()
    assert "remarques" in serializer.errors

@pytest.mark.django_db
def test_client_serializer_type_visa_required_if_a_un_visa():
    """
    Teste la validation croisée : type_visa obligatoire si a_un_visa = True.
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    data = {
        "adresse": "10 rue",
        "ville": "Paris",
        "code_postal": "75001",
        "a_un_visa": True,
        "type_visa": ""
    }
    serializer = ClientSerializer(data=data)
    assert not serializer.is_valid()
    assert "type_visa" in serializer.errors

@pytest.mark.django_db
def test_client_serializer_full_ok():
    """
    Teste la création complète d'un client avec tous les champs valides.
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0600000000", status_id=1)
    service = Service.objects.create(label="Naturalisation", code="NAT")
    data = {
        "adresse": "10 rue",
        "ville": "Paris",
        "code_postal": "75001",
        "date_naissance": "1990-01-01",
        "a_un_visa": True,
        "type_visa": "SCHENGEN",
        "remarques": "RAS",
        "type_demande_id": service.id,
    }
    serializer = ClientSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    client = serializer.save(lead=lead)
    assert client.type_demande == service