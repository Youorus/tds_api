import logging
import smtplib
from datetime import datetime

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from api.models import User
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

    def send_appointment_planned(self, lead):
        print(f"[📨 PLANIFICATION] Envoi à : {lead.appointment_date}")
        context = {
            "user": lead,
            "appointment": get_formatted_appointment(lead.appointment_date),
            "year": datetime.now().year,
        }
        return self.send_html_email(
            to_email=lead.email,
            subject="Votre rendez-vous chez TDS France a été planifié",
            template_name="email/appointment_planned.html",
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

    def send_formulaire_email(self, lead):
        name_param = f"{lead.first_name} {lead.last_name}".replace(" ", "%20")
        formulaire_url = f"{settings.FRONTEND_BASE_URL}/formulaire?id={lead.id}&name={name_param}"

        context = {
            "user": lead,
            "formulaire_url": formulaire_url,
            "year": datetime.now().year,
        }

        return self.send_html_email(
            to_email=lead.email,
            subject="Merci de compléter votre formulaire – TDS France",
            template_name="email/formulaire_link.html",
            context=context,
        )
    def send_lead_assignment_request_to_admin(self, conseiller, lead):
        """Send assignment request email to all admins"""

        context = {
            "conseiller": conseiller,
            "lead": lead,
            "year": datetime.now().year,
        }

        subject = f"Demande d'assignation – {conseiller.first_name} {conseiller.last_name}"

        admin_emails = [
            admin.email for admin in User.objects.filter(role=User.Roles.ADMIN) if admin.email
        ]

        for admin_email in admin_emails:
            self.send_html_email(
                to_email=admin_email,
                subject=subject,
                template_name="email/lead_assignment_request_admin.html",
                context=context,
            )

    def send_lead_assignment_confirmation_to_conseiller(self, conseiller, lead):
        """Send confirmation email to the conseiller"""
        context = {
            "conseiller": conseiller,
            "lead": lead,
            "year": datetime.now().year,
        }

        subject = f"Lead assigné – {lead.first_name} {lead.last_name}"

        return self.send_html_email(
            to_email=conseiller.email,
            subject=subject,
            template_name="email/lead_assignment_confirmation_conseiller.html",
            context=context,
        )
