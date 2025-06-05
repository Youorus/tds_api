# services/notification_service.py

from .email_service import EmailService
from .whatsapp_service import WhatsAppService

class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.whatsapp_service = WhatsAppService()

    def send_appointment_confirmation(self, lead):
        return self.email_service.send_appointment_confirmation(lead)

    def send_appointment_reminder(self, lead):
        return self.email_service.send_appointment_reminder(lead)

    def send_missed_appointment(self, lead):
        return self.email_service.send_missed_appointment(lead)

    def send_welcome(self, lead):
        return self.email_service.send_welcome_email(lead)

    def send_lead_assignment_request_to_admin(self, conseiller, lead):
        """Send assignment request to all admins"""
        return self.email_service.send_lead_assignment_request_to_admin(conseiller, lead)

    def send_lead_assignment_confirmation_to_conseiller(self, conseiller, lead):
        """Send assignment confirmation to the conseiller"""
        return self.email_service.send_lead_assignment_confirmation_to_conseiller(conseiller, lead)