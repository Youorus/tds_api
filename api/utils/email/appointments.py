# api/utils/email/appointments.py

from datetime import datetime
from babel.dates import format_datetime
from django.utils import timezone

from api.utils.email.core import send_html_email


def get_french_datetime_strings(dt):
    """
    Prend un datetime (aware) et retourne la date/heure formatée en français, fuseau local.
    """
    dt_local = timezone.localtime(dt)
    # "EEEE" = nom du jour, "d MMMM yyyy" = ex: mardi 31 juillet 2025
    date_str = format_datetime(dt_local, "EEEE d MMMM yyyy", locale="fr_FR")
    time_str = format_datetime(dt_local, "HH:mm", locale="fr_FR")
    return date_str, time_str


def send_appointment_confirmation_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,     # Ex: mardi 31 juillet 2025
            "time": time_str,     # Ex: 14:30
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous chez TDS France est confirmé",
        template_name="email/appointment_confirmation.html",
        context=context,
    )


def send_appointment_reminder_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Rappel : votre rendez-vous avec TDS France",
        template_name="email/appointment_reminder.html",
        context=context,
    )


def send_missed_appointment_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
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
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Bienvenue chez TDS France ",
        template_name="email/welcome.html",
        context=context,
    )


def send_appointment_planned_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous a été planifié chez TDS France",
        template_name="email/appointment_planned.html",
        context=context,
    )


def send_jurist_appointment_email(jurist_appointment):
    """
    Envoie un email de confirmation de RDV juriste (suivi de dossier).
    """
    lead = jurist_appointment.lead
    jurist = jurist_appointment.jurist
    date_str, time_str = get_french_datetime_strings(jurist_appointment.date)
    context = {
        "user": lead,
        "jurist": jurist,
        "appointment": {
            "date": date_str,   # Ex: mardi 30 juillet 2025
            "time": time_str,   # Ex: 14:30
            "location": "11 rue de l'Arrivée, 75015 Paris (En face du magasin C&A, dans la galerie)",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous de suivi de dossier – TDS France",
        template_name="email/jurist_appointment_planned.html",
        context=context,
    )


def send_appointment_created_or_updated_email(lead, appointment_date, is_update=False):
    date_str, time_str = get_french_datetime_strings(appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
    }
    subject = (
        "Modification de votre rendez-vous chez TDS France"
        if is_update else
        "Votre rendez-vous a été planifié chez TDS France"
    )
    template_name = (
        "email/appointment_updated.html"
        if is_update else
        "email/appointment_created.html"
    )
    send_html_email(
        to_email=lead.email,
        subject=subject,
        template_name=template_name,
        context=context,
    )

def send_appointment_deleted_email(lead, appointment_date):
    date_str, time_str = get_french_datetime_strings(appointment_date)
    context = {
        "user": lead,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous – TDS France",
        template_name="email/appointment_deleted.html",
        context=context,
    )

def send_jurist_appointment_deleted_email(lead, jurist, appointment_date):
    """
    Email envoyé au client lors de l’annulation d’un rendez-vous juriste.
    """
    date_str, time_str = get_french_datetime_strings(appointment_date)
    context = {
        "user": lead,
        "jurist": jurist,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris (En face du magasin C&A, dans la galerie)",
        },
        "year": timezone.now().year,
    }
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous juriste – TDS France",
        template_name="email/jurist_appointment_deleted.html",
        context=context,
    )