from background_task import background
from django.utils.timezone import now
from datetime import timedelta

from api.models import Lead, LeadStatus
from api.services.notification_service import NotificationService

notification_service = NotificationService()

@background(schedule=60)  # le paramètre est optionnel ici
def send_rdv_reminders_bg():
    """Envoie un rappel aux leads ayant un RDV demain."""
    tomorrow = now().date() + timedelta(days=1)
    leads = Lead.objects.filter(appointment_date__date=tomorrow)
    for lead in leads:
        notification_service.send_appointment_reminder(lead)
    print(f"{leads.count()} rappels envoyés.")
    return f"{leads.count()} rappels envoyés."


@background(schedule=60)
def maj_leads_absents_auto_bg():
    """
    Met à jour les leads ayant un RDV PLANIFIÉ, absents depuis >1h, et notifie.
    """
    limite = now() - timedelta(hours=1)
    try:
        status_rdv_planifie = LeadStatus.objects.get(code="RDV_PLANIFIE")
        status_absent = LeadStatus.objects.get(code="ABSENT")
    except LeadStatus.DoesNotExist:
        print("Statuts RDV_PLANIFIE ou ABSENT introuvables")
        return "Statuts RDV_PLANIFIE ou ABSENT introuvables"

    leads = Lead.objects.filter(status=status_rdv_planifie, appointment_date__lt=limite)
    updated_count = 0
    for lead in leads:
        lead.status = status_absent
        lead.save()
        notification_service.send_missed_appointment(lead)
        updated_count += 1
    print(f"{updated_count} leads mis à jour en 'absent'")
    return f"{updated_count} leads mis à jour en 'absent'"