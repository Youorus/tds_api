from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from django.utils.timezone import make_aware

from api.lead_status.models import LeadStatus
from api.leads.constants import ABSENT, RDV_CONFIRME
from api.leads.models import Lead
from api.leads.tasks import mark_absent_leads, send_reminder_emails


@pytest.mark.django_db
@patch("api.leads.tasks.send_appointment_reminder_email")
def test_send_reminder_emails_j1(mock_send_email):
    """
    Teste l'envoi du rappel 1 jour avant le RDV.
    """
    status = LeadStatus.objects.create(code=RDV_CONFIRME, label="RDV confirmé")
    lead = Lead.objects.create(
        first_name="Test",
        last_name="Demain",
        email="test@example.com",
        phone="+33612345678",
        status=status,
        appointment_date=timezone.now() + timedelta(days=1),
    )

    send_reminder_emails()

    mock_send_email.assert_called_once_with(lead)


@pytest.mark.django_db
@patch("api.leads.tasks.send_missed_appointment_email")
def test_mark_absent_leads(mock_send_email):
    """
    Teste la mise à jour en 'ABSENT' + l'envoi du mail si le RDV est passé.
    """
    status_confirmed = LeadStatus.objects.create(
        code=RDV_CONFIRME, label="RDV confirmé"
    )
    status_absent = LeadStatus.objects.create(code=ABSENT, label="Absent")

    lead = Lead.objects.create(
        first_name="Test",
        last_name="Absent",
        email="test@example.com",
        phone="+33612345678",
        status=status_confirmed,
        appointment_date=timezone.now() - timedelta(hours=3),
    )

    mark_absent_leads()

    lead.refresh_from_db()
    assert lead.status == status_absent
    mock_send_email.assert_called_once_with(lead)
