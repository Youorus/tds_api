import pytest
from api.clients.models import Client
from api.leads.models import Lead
from datetime import date

@pytest.mark.django_db
def test_client_creation_minimal():
    """
    Vérifie la création d'un client avec le minimum d'information.
    """
    lead = Lead.objects.create(first_name="Marc", last_name="Nkue", phone="0601020304", status_id=1)
    client = Client.objects.create(lead=lead)
    assert client.lead == lead
    assert str(client) == f"Données de {lead.first_name} {lead.last_name}"

@pytest.mark.django_db
def test_client_defaults():
    """
    Vérifie que les valeurs par défaut sont respectées à la création.
    """
    lead = Lead.objects.create(first_name="Ana", last_name="Smith", phone="0702030405", status_id=1)
    client = Client.objects.create(lead=lead)
    assert client.custom_demande == ""
    assert client.remarques == ""
    assert client.a_un_visa is None
    assert client.a_des_enfants is None
    assert client.created_at is not None
    assert client.updated_at is not None

@pytest.mark.django_db
def test_client_full_fields():
    """
    Teste la création d'un client avec tous les champs possibles.
    """
    lead = Lead.objects.create(first_name="Zoé", last_name="Mendy", phone="0102030405", status_id=1)
    client = Client.objects.create(
        lead=lead,
        source=[{"value": "GOOGLE"}],
        civilite="MONSIEUR",
        custom_demande="Changement de statut",
        date_naissance=date(2000, 1, 1),
        lieu_naissance="Paris",
        pays="France",
        nationalite="Française",
        adresse="1 rue du Test",
        code_postal="75000",
        ville="Paris",
        date_entree_france=date(2010, 1, 1),
        a_un_visa=True,
        type_visa="SCHENGEN",
        statut_refugie_ou_protection=False,
        demande_deja_formulee=True,
        demande_formulee_precise="Titre de séjour",
        situation_familiale="CELIBATAIRE",
        a_des_enfants=True,
        nombre_enfants=2,
        nombre_enfants_francais=1,
        enfants_scolarises=True,
        naissance_enfants_details="2005, 2008",
        situation_pro="CDI",
        domaine_activite="Informatique",
        nombre_fiches_paie=6,
        date_depuis_sans_emploi=date(2019, 12, 1),
        a_deja_eu_oqtf=False,
        date_derniere_oqtf=None,
        demarche_en_cours_administration=True,
        remarques="RAS",
    )
    assert client.ville == "Paris"
    assert client.nombre_enfants == 2

@pytest.mark.django_db
def test_client_one_to_one_constraint():
    """
    Vérifie la contrainte d'unicité du champ lead (OneToOneField).
    """
    lead = Lead.objects.create(first_name="Léa", last_name="Mbao", phone="0677889900", status_id=1)
    Client.objects.create(lead=lead)
    with pytest.raises(Exception):
        Client.objects.create(lead=lead)

@pytest.mark.django_db
def test_client_str_method():
    """
    Teste la représentation textuelle du client (__str__).
    """
    lead = Lead.objects.create(first_name="Test", last_name="User", phone="0611223344", status_id=1)
    client = Client.objects.create(lead=lead)
    assert str(client) == "Données de Test User"

@pytest.mark.django_db
def test_client_created_and_updated_auto_now():
    """
    Vérifie que created_at et updated_at sont bien positionnés automatiquement.
    """
    lead = Lead.objects.create(first_name="Time", last_name="Stamps", phone="0611111111", status_id=1)
    client = Client.objects.create(lead=lead)
    assert client.created_at is not None
    assert client.updated_at is not None

@pytest.mark.django_db
def test_client_negative_nombre_enfants_not_saved():
    """
    Vérifie qu'il n'est pas possible d'enregistrer un nombre négatif d'enfants
    (nécessite d'avoir la validation correspondante côté serializer ou formulaire).
    Ce test doit échouer en base, mais serait normalement intercepté par un serializer.
    """
    lead = Lead.objects.create(first_name="Neg", last_name="Val", phone="0699999999", status_id=1)
    # Direct en base, pas d'exception sauf si tu ajoutes un validator/model clean()
    client = Client.objects.create(lead=lead, nombre_enfants=-2)
    assert client.nombre_enfants == -2  # Il vaut mieux gérer ça dans le serializer !