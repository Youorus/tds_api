import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from api.lead_status.models import LeadStatus
from api.leads.constants import ABSENT, RDV_CONFIRME
from api.leads.models import Lead
from api.utils.email import (
    send_appointment_reminder_email,
    send_missed_appointment_email,
)

logger = logging.getLogger(__name__)


@shared_task
def send_reminder_emails():
    """
    Tâche pour envoyer des e-mails de rappel aux leads avec un rendez-vous confirmé :
    - J-1 : un jour avant le rendez-vous.
    - H-2 : deux heures avant le rendez-vous.
    ⚠️ Protection anti-doublons via `last_reminder_sent` (≥ 1h entre deux envois).
    """
    now = timezone.now()

    # Fenêtre J-1 : entre J-1 pile et J-1 + 1h
    one_day_start = now + timedelta(days=1)
    one_day_end = one_day_start + timedelta(hours=1)

    # Fenêtre H-2 : entre H-2 pile et H-2 + 1h
    two_hours_start = now + timedelta(hours=2)
    two_hours_end = two_hours_start + timedelta(hours=1)

    # Leads avec RDV confirmé
    leads = Lead.objects.filter(status__code=RDV_CONFIRME)

    leads_to_remind = leads.filter(
        appointment_date__range=(one_day_start, one_day_end)
    ) | leads.filter(
        appointment_date__range=(two_hours_start, two_hours_end)
    )

    for lead in leads_to_remind.distinct():
        # Protection anti-spam (≥ 1h entre 2 rappels)
        if not lead.last_reminder_sent or (now - lead.last_reminder_sent).total_seconds() > 3600:
            send_appointment_reminder_email(lead)
            lead.last_reminder_sent = now
            lead.save(update_fields=["last_reminder_sent"])
            logger.info(f"📧 Rappel envoyé à {lead.email} (lead #{lead.id})")
        else:
            logger.info(f"⏩ Lead #{lead.id} déjà rappelé récemment, skip.")


@shared_task
def mark_absent_leads():
    """
    Tâche pour marquer comme absents les leads dont le rendez-vous confirmé est déjà passé.
    Un mail d'absence est envoyé si l'email du lead est présent.
    """
    now = timezone.now()

    try:
        absent_status = LeadStatus.objects.get(code=ABSENT)
        confirmed_status = LeadStatus.objects.get(code=RDV_CONFIRME)
    except LeadStatus.DoesNotExist:
        logger.error("❌ Statuts 'ABSENT' ou 'RDV_CONFIRME' introuvables.")
        return

    leads_to_mark = Lead.objects.filter(status=confirmed_status, appointment_date__lt=now)

    for lead in leads_to_mark:
        lead.status = absent_status
        lead.save(update_fields=["status"])
        logger.info(f"✅ Lead #{lead.id} marqué comme ABSENT")

        if lead.email:
            send_missed_appointment_email(lead)
            logger.info(f"📧 Mail d'absence envoyé à {lead.email} (lead #{lead.id})")
        else:
            logger.warning(f"⚠️ Email manquant pour lead #{lead.id}, pas d'envoi possible.")