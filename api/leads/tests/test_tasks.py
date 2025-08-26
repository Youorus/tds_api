# """
# Tests unitaires pour les tâches automatisées liées aux leads.
#
# - `send_reminder_emails` : envoie des e-mails de rappel 1 jour et 2h avant le rendez-vous.
# - `mark_absent_leads` : marque les leads avec un rendez-vous passé comme absents.
#
# Ces tests vérifient que :
# - Les statuts sont correctement mis à jour.
# - Les rappels ne sont envoyés qu'aux leads avec un statut confirmé.
# - Les appels à `NotificationService` sont effectués correctement.
# """
# api/leads/tests/test_tasks.py

import pytest
from datetime import timedelta, datetime
from django.utils import timezone
from api.leads.models import Lead
from api.leads.tasks import mark_absent_leads, send_reminder_emails
from api.lead_status.models import LeadStatus
from api.leads.constants import RDV_CONFIRME, ABSENT
from unittest import mock

pytestmark = pytest.mark.django_db


@pytest.fixture
def lead_status_confirmed():
    return LeadStatus.objects.create(code=RDV_CONFIRME, label="RDV confirmé", color="#0000ff")


@pytest.fixture
def lead_status_absent():
    return LeadStatus.objects.create(code=ABSENT, label="Absent", color="#ff0000")


@pytest.fixture
def lead_confirmed_past(lead_status_confirmed):
    return Lead.objects.create(
        first_name="John",
        last_name="Doe",
        email="past@example.com",
        appointment_date=timezone.now() - timedelta(hours=3),
        status=lead_status_confirmed,
    )


def test_mark_absent_leads_updates_correct_leads(lead_confirmed_past, lead_status_absent):
    # Exécuter la tâche
    mark_absent_leads()

    # Rafraîchir l'objet depuis la base de données
    lead_confirmed_past.refresh_from_db()

    # Vérifier que le statut a été mis à jour
    assert lead_confirmed_past.status.code == ABSENT


@mock.patch("api.leads.tasks.notification_service.send_appointment_reminder")
@mock.patch("api.leads.tasks.timezone")
def test_send_reminder_emails_calls_correct_methods(mock_timezone, mock_send, lead_status_confirmed):
    # Définir une date fixe avec le bon timezone
    fixed_now = timezone.make_aware(datetime(2025, 8, 26, 10, 0, 0))
    mock_timezone.now.return_value = fixed_now

    # Créer un lead avec rendez-vous dans 1 jour (même date mais heure différente)
    lead_1d = Lead.objects.create(
        first_name="Tomorrow",
        last_name="Lead",
        email="tomorrow@example.com",
        appointment_date=fixed_now + timedelta(days=1),
        status=lead_status_confirmed,
    )

    # Créer un lead avec rendez-vous dans 2 heures (même date)
    lead_2h = Lead.objects.create(
        first_name="Soon",
        last_name="Lead",
        email="soon@example.com",
        appointment_date=fixed_now + timedelta(hours=2),
        status=lead_status_confirmed,
    )

    # Exécuter la tâche
    send_reminder_emails()

    # Vérifier que les emails ont été envoyés
    assert mock_send.call_count == 2

    # Vérifier que les bons emails ont été appelés
    called_emails = {call.args[0].email for call in mock_send.call_args_list}
    assert called_emails == {"tomorrow@example.com", "soon@example.com"}


# Test supplémentaire pour vérifier qu'aucun rappel n'est envoyé pour les leads non confirmés
@mock.patch("api.leads.tasks.notification_service.send_appointment_reminder")
@mock.patch("api.leads.tasks.timezone")
def test_send_reminder_emails_ignores_non_confirmed_leads(mock_timezone, mock_send, lead_status_confirmed):
    fixed_now = timezone.make_aware(datetime(2025, 8, 26, 10, 0, 0))
    mock_timezone.now.return_value = fixed_now

    # Créer un autre statut (non confirmé)
    other_status = LeadStatus.objects.create(code="OTHER", label="Autre", color="#00ff00")

    # Créer un lead avec statut non confirmé mais date correspondante
    Lead.objects.create(
        first_name="Other",
        last_name="Status",
        email="other@example.com",
        appointment_date=fixed_now + timedelta(days=1),
        status=other_status,
    )

    send_reminder_emails()

    # Vérifier qu'aucun email n'a été envoyé
    assert mock_send.call_count == 0