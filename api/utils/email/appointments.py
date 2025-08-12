# api/utils/email/appointments.py

from django.utils import timezone
from babel.dates import format_datetime

from api.utils.email.core import send_html_email


# ---------------------------------
# Helpers
# ---------------------------------

def get_french_datetime_strings(dt):
    """Retourne (date_str, time_str) en français, en timezone locale."""
    dt_local = timezone.localtime(dt)
    date_str = format_datetime(dt_local, "EEEE d MMMM yyyy", locale="fr_FR")
    time_str = format_datetime(dt_local, "HH:mm", locale="fr_FR")
    return date_str, time_str


def _base_context(lead: object) -> dict:
    """Contexte commun utilisé par tous les e‑mails."""
    return {
        "user": lead,
        "year": timezone.now().year,
    }


def _name_from_user(user) -> str | None:
    """Construit un nom affichable à partir d'un objet utilisateur (juriste/conseiller)."""
    if not user:
        return None
    fn = (getattr(user, "first_name", "") or "").strip()
    ln = (getattr(user, "last_name", "") or "").strip()
    if fn or ln:
        return f"{fn} {ln}".strip()
    return getattr(user, "username", None) or getattr(user, "email", None)


def _get_with_info(appointment) -> tuple[str | None, str | None]:
    """
    Détermine avec qui a lieu le rendez‑vous.
    - RDV juriste: appointment.jurist
    - RDV classique: appointment.created_by, sinon appointment.lead.assigned_to
    Retourne (label, name) ou (None, None) si inconnu.
    """
    label = None
    user = None

    if hasattr(appointment, "jurist") and getattr(appointment, "jurist"):
        label = "Juriste"
        user = appointment.jurist
    elif hasattr(appointment, "created_by") and getattr(appointment, "created_by"):
        label = "Conseiller"
        user = appointment.created_by
    elif hasattr(appointment, "lead") and getattr(appointment.lead, "assigned_to", None):
        label = "Conseiller"
        user = appointment.lead.assigned_to

    return label, _name_from_user(user)


# ---------------------------------
# Emails
# ---------------------------------

def send_appointment_confirmation_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
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
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
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
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="⚠️ Vous avez manqué votre rendez-vous – TDS France",
        template_name="email/appointment_missed.html",
        context=context,
    )


def send_welcome_email(lead):
    context = _base_context(lead)
    send_html_email(
        to_email=lead.email,
        subject="Bienvenue chez TDS France ",
        template_name="email/welcome.html",
        context=context,
    )


def send_appointment_planned_email(lead):
    date_str, time_str = get_french_datetime_strings(lead.appointment_date)
    context = {
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous a été planifié chez TDS France",
        template_name="email/appointment_planned.html",
        context=context,
    )


def send_jurist_appointment_email(jurist_appointment):
    """Email de confirmation de RDV juriste (suivi de dossier)."""
    lead = jurist_appointment.lead
    jurist = jurist_appointment.jurist
    date_str, time_str = get_french_datetime_strings(jurist_appointment.date)
    label, name = "Juriste", _name_from_user(jurist)
    context = {
        **_base_context(lead),
        "jurist": jurist,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris (En face du magasin C&A, dans la galerie)",
            "with_label": label,
            "with_name": name or "",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous de suivi de dossier – TDS France",
        template_name="email/jurist_appointment_planned.html",
        context=context,
    )


def send_appointment_created_or_updated_email(lead, appointment, is_update=False):
    date_str, time_str = get_french_datetime_strings(appointment.date)
    with_label, with_name = _get_with_info(appointment)
    context = {
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
            "note": appointment.note or "",
            "with_label": with_label or "Avec",
            "with_name": with_name or "",
        },
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


def send_appointment_deleted_email(lead, appointment_date, appointment=None):
    """
    Email d'annulation. Si `appointment` est fourni, on inclut "avec qui".
    Signature rétro‑compatible : l'ancien appel (lead, date) reste valide.
    """
    date_str, time_str = get_french_datetime_strings(appointment_date)
    with_label, with_name = (None, None)
    if appointment is not None:
        with_label, with_name = _get_with_info(appointment)

    context = {
        **_base_context(lead),
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris",
            "with_label": with_label or "Avec",
            "with_name": with_name or "",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous – TDS France",
        template_name="email/appointment_deleted.html",
        context=context,
    )


def send_jurist_appointment_deleted_email(lead, jurist, appointment_date):
    """Email au client lors de l’annulation d’un rendez-vous juriste."""
    date_str, time_str = get_french_datetime_strings(appointment_date)
    label, name = "Juriste", _name_from_user(jurist)
    context = {
        **_base_context(lead),
        "jurist": jurist,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": "11 rue de l'Arrivée, 75015 Paris (En face du magasin C&A, dans la galerie)",
            "with_label": label,
            "with_name": name or "",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous juriste – TDS France",
        template_name="email/jurist_appointment_deleted.html",
        context=context,
    )