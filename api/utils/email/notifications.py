from django_extensions.management.shells import import_items

from api.utils.email.appointments import (
    send_appointment_confirmation_email,
    send_appointment_reminder_email,
    send_missed_appointment_email,
    send_welcome_email,
    send_appointment_planned_email,  # ← ajoute ici
)
from api.utils.email.leads import (
    send_lead_assignment_request_to_admin,
    send_lead_assignment_confirmation_to_conseiller,
    send_formulaire_email, send_dossier_status_email
)


class NotificationService:
    """
    Service central pour orchestrer tous les emails métiers.
    """
    def send_appointment_confirmation(self, lead):
        send_appointment_confirmation_email(lead)

    def send_appointment_reminder(self, lead):
        send_appointment_reminder_email(lead)

    def send_missed_appointment(self, lead):
        send_missed_appointment_email(lead)

    def send_appointment_planned(self, lead):  # ← méthode pour "rendez-vous planifié"
        send_appointment_planned_email(lead)

    def send_welcome(self, lead):
        send_welcome_email(lead)

    def send_lead_assignment_request_to_admin(self, conseiller, lead):
        send_lead_assignment_request_to_admin(conseiller, lead)

    def send_lead_assignment_confirmation_to_conseiller(self, conseiller, lead):
        send_lead_assignment_confirmation_to_conseiller(conseiller, lead)

    def send_lead_formulaire(self, lead):
        send_formulaire_email(self, lead)

    def send_dossier_status_notification(self, lead):
        send_dossier_status_email(lead)
