from .email_service import EmailService
from .whatsapp_service import WhatsAppService

class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.whatsapp_service = WhatsAppService()

    def send_appointment_confirmation(self, lead):
        """Envoie confirmation par email et WhatsApp"""
        email_sent = self.email_service.send_appointment_confirmation(lead)
        #whatsapp_sent = self.whatsapp_service.send_appointment_confirmation(lead)
        return email_sent

    def send_appointment_reminder(self, lead):
        """Envoie rappel par email et WhatsApp"""
        email_sent = self.email_service.send_appointment_reminder(lead)
        #whatsapp_sent = self.whatsapp_service.send_appointment_reminder(lead)
        return email_sent

    def send_missed_appointment(self, lead):
        """Envoie notification d'absence par email"""
        return self.email_service.send_missed_appointment(lead)

    def send_welcome(self, lead):
        """Envoie email de bienvenue"""
        return self.email_service.send_welcome_email(lead)