import logging
import smtplib
from datetime import datetime

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from api.utils.utils import get_formatted_appointment

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.default_from_email = settings.DEFAULT_FROM_EMAIL

    def send_html_email(self, to_email, subject, template_name, context):
        """Envoie un email HTML"""
        if not to_email:
            logger.warning("Aucun email fourni.")
            return False

        try:
            html_content = render_to_string(template_name, context)

            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body="",
                    from_email=self.default_from_email,
                    to=[to_email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            logger.info(f"Email envoyé avec succès à {to_email}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur générale: {str(e)}")
            return False

    def send_appointment_confirmation(self, lead):
        print(f"[📨 CONFIRMATION] Envoi à : {lead.appointment_date}")
        context = {
            "user": lead,
            "appointment": get_formatted_appointment(lead.appointment_date),
            "year": datetime.now().year,
        }
        return self.send_html_email(
            to_email=lead.email,
            subject="Votre rendez-vous chez TDS France est confirmé",
            template_name="email/appointment_confirmation.html",
            context=context,
        )

    def send_appointment_reminder(self, lead):
        print(f"[📨 RAPPEL] Envoi à : {lead.email}")
        context = {
            "user": lead,
            "appointment": get_formatted_appointment(lead.appointment_date),
            "year": datetime.now().year,
        }
        return self.send_html_email(
            to_email=lead.email,
            subject="Rappel : votre rendez-vous avec TDS France",
            template_name="email/appointment_reminder.html",
            context=context,
        )

    def send_missed_appointment(self, lead):
        print(f"[📨 ABSENT] Envoi à : {lead.email}")
        context = {
            "user": lead,
            "appointment": get_formatted_appointment(lead.appointment_date),
            "year": datetime.now().year,
        }
        return self.send_html_email(
            to_email=lead.email,
            subject="Vous avez manqué votre rendez-vous – TDS France",
            template_name="email/appointment_missed.html",
            context=context,
        )

    def send_welcome_email(self, lead):
        print(f"[📨 WELCOME] Envoi à : {lead.email}")
        context = {
            "user": lead,
            "year": datetime.now().year,
        }
        return self.send_html_email(
            to_email=lead.email,
            subject="Bienvenue chez TDS France",
            template_name="email/welcome.html",
            context=context,
        )