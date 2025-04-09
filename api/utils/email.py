import locale
import logging
import smtplib
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # Pour avoir les noms des jours/mois en français

def send_html_email(to_email, subject, template_name, context):
    if not to_email:
        logger.warning("Aucun email fourni.")
        return

    try:
        html_content = render_to_string(template_name, context)

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

            msg = EmailMultiAlternatives(
                subject=subject,
                body="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        logger.info(f"Email envoyé avec succès à {to_email}")

    except smtplib.SMTPException as e:
        logger.error(f"Erreur SMTP: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur générale: {str(e)}")
        raise



def send_appointment_confirmation_email(lead):
    context = {
        "user": lead,
        "appointment": {
            "date": lead.appointment_date.strftime("%A %d %B %Y"),
            "time": lead.appointment_date.strftime("%H:%M"),
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": datetime.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous chez TDS France est confirmé",
        template_name="email/appointment_confirmation.html",
        context=context,
    )

def send_appointment_reminder_email(lead):
    context = {
        "user": lead,
        "appointment": {
            "date": lead.appointment_date.strftime("%A %d %B %Y"),
            "time": lead.appointment_date.strftime("%H:%M"),
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": datetime.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Rappel : votre rendez-vous avec TDS France",
        template_name="email/appointment_reminder.html",
        context=context,
    )


def send_missed_appointment_email(lead):
    context = {
        "user": lead,
        "appointment": {
            "date": lead.appointment_date.strftime("%A %d %B %Y"),
            "time": lead.appointment_date.strftime("%H:%M"),
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": datetime.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="⚠️ Vous avez manqué votre rendez-vous – TDS France",
        template_name="email/appointment_missed.html",
        context=context,
    )

def send_welcome_email(lead):
    context = {
        "user": lead,
        "year": datetime.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Bienvenue chez TDS France ",
        template_name="email/welcome.html",
        context=context,
    )