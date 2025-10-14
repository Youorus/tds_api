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
@shared_task
def send_reminder_emails():
    """
    Envoie un rappel un jour avant le rendez-vous confirmé.
    """
    now = timezone.now()
    tomorrow = now.date() + timedelta(days=1)

    leads = Lead.objects.filter(
        status__code=RDV_CONFIRME,
        appointment_date__date=tomorrow
    )

    for lead in leads:
        if not lead.last_reminder_sent:
            send_appointment_reminder_email(lead)
            lead.last_reminder_sent = now
            lead.save(update_fields=["last_reminder_sent"])
            logger.info(f"📧 Rappel J-1 envoyé à {lead.email} (lead #{lead.id})")


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