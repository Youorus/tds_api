# api/utils/email/appointments.py
from datetime import datetime

from api.utils.email.core import send_html_email


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

def send_appointment_planned_email(lead):
    """
    Envoie un email lorsqu'un rendez-vous vient d'être planifié (statut RDV_PLANIFIE).
    Utilise le template email/appointment_planned.html.
    """
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
        subject="Votre rendez-vous a été planifié chez TDS France",
        template_name="email/appointment_planned.html",
        context=context,
    )