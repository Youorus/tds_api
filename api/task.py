from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta

from api.models import Lead, LeadStatus
from api.services import NotificationService

notification_service = NotificationService()

@shared_task
def send_rdv_reminders():
    """Envoie un rappel aux leads ayant un RDV demain."""
    tomorrow = now().date() + timedelta(days=1)
    leads = Lead.objects.filter(appointment_date__date=tomorrow)
    for lead in leads:
        notification_service.send_appointment_reminder(lead)
    return f"{leads.count()} rappels envoyés."

@shared_task
def maj_leads_absents_auto():
    """Met à jour les leads RDV_CONFIRME absents depuis >1h et notifie."""
    limite = now() - timedelta(hours=1)
    leads = Lead.objects.filter(status=LeadStatus.RDV_CONFIRME, appointment_date__lt=limite)
    updated_count = 0
    for lead in leads:
        lead.status = LeadStatus.ABSENT
        lead.save()
        notification_service.send_missed_appointment(lead)
        updated_count += 1
    return f"{updated_count} leads mis à jour en 'absent'"