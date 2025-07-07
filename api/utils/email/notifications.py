from api.utils.email.appointments import (
    send_appointment_confirmation_email,
    send_appointment_reminder_email,
    send_missed_appointment_email,
    send_welcome_email,
)
from api.utils.email.leads import (
    send_lead_assignment_request_to_admin,
    send_lead_assignment_confirmation_to_conseiller,
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

    def send_welcome(self, lead):
        send_welcome_email(lead)

    def send_lead_assignment_request_to_admin(self, conseiller, lead):
        send_lead_assignment_request_to_admin(conseiller, lead)

    def send_lead_assignment_confirmation_to_conseiller(self, conseiller, lead):
        send_lead_assignment_confirmation_to_conseiller(conseiller, lead)