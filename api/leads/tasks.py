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


"""
Tâche périodique pour envoyer des e-mails de rappel aux leads avec un rendez-vous confirmé :
- Un rappel est envoyé 1 jour avant le rendez-vous.
- Un autre rappel est envoyé 2 heures avant le rendez-vous.
"""


@shared_task
def send_reminder_emails():
    now = timezone.now()

    # Rappel 1 jour avant
    one_day_later = now + timedelta(days=1)
    leads_1d = Lead.objects.filter(
        status__code=RDV_CONFIRME, appointment_date__date=one_day_later.date()
    )

    for lead in leads_1d:
        send_appointment_reminder_email(lead)
        logger.info(f"📧 Rappel J-1 envoyé à {lead.email} (lead #{lead.id})")

    # Rappel 2h avant
    two_hours_later = now + timedelta(hours=2)
    leads_2h = Lead.objects.filter(
        status__code=RDV_CONFIRME,
        appointment_date__hour=two_hours_later.hour,
        appointment_date__date=two_hours_later.date(),
        minute__minute=two_hours_later.minute,
    )

    for lead in leads_2h:
        send_appointment_reminder_email(lead)
        logger.info(f"📧 Rappel H-2 envoyé à {lead.email} (lead #{lead.id})")


"""
Tâche périodique pour marquer comme absents les leads dont le rendez-vous confirmé est déjà passé.
Et envoyer un e-mail d'absence à chaque lead concerné.
"""


@shared_task
def mark_absent_leads():
    now = timezone.now()

    try:
        absent_status = LeadStatus.objects.get(code=ABSENT)
        confirmed_status = LeadStatus.objects.get(code=RDV_CONFIRME)
    except LeadStatus.DoesNotExist:
        logger.error("❌ Les statuts 'ABSENT' ou 'RDV_CONFIRME' sont introuvables.")
        return

    leads_to_mark = Lead.objects.filter(
        status=confirmed_status, appointment_date__lt=now
    )

    for lead in leads_to_mark:
        lead.status = absent_status
        lead.save()
        logger.info(f"✅ Lead #{lead.id} marqué comme ABSENT")

        if lead.email:
            send_missed_appointment_email(lead)
            logger.info(f"📧 Mail d'absence envoyé à {lead.email} (lead #{lead.id})")
        else:
            logger.warning(
                f"⚠️ Impossible d'envoyer le mail d'absence (email manquant) pour lead #{lead.id}"
            )
