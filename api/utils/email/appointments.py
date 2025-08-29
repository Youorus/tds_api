# api/utils/email/notifications.py
from PIL.TiffImagePlugin import COPYRIGHT

from api.utils.email import send_html_email

from api.utils.email.config import TDS_FRANCE_ADDRESS, _base_context, _build_context
from api.utils.email.utils import get_french_datetime_strings, _name_from_user


def send_jurist_appointment_email(jurist_appointment):
    lead = jurist_appointment.lead
    context = _build_context(
        lead,
        jurist_appointment.date,
        TDS_FRANCE_ADDRESS,
        COPYRIGHT,
        appointment=jurist_appointment,
        is_jurist=True,
    )
    send_html_email(
        to_email=lead.email,
        subject="Votre rendez-vous de suivi de dossier – TDS France",
        template_name="email/jurist_appointment_planned.html",
        context=context,
    )


def send_appointment_created_or_updated_email(lead, appointment, is_update=False):
    context = _build_context(lead, appointment.date, TDS_FRANCE_ADDRESS, appointment=appointment)
    send_html_email(
        to_email=lead.email,
        subject=(
            "Modification de votre rendez-vous chez TDS France"
            if is_update else "Votre rendez-vous a été planifié chez TDS France"
        ),
        template_name=(
            "email/appointment_updated.html"
            if is_update else "email/appointment_created.html"
        ),
        context=context,
    )


def send_appointment_deleted_email(lead, appointment_date, appointment=None):
    context = _build_context(lead, appointment_date, TDS_FRANCE_ADDRESS, appointment=appointment)
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous – TDS France",
        template_name="email/appointment_deleted.html",
        context=context,
    )


def send_jurist_appointment_deleted_email(lead, jurist, appointment_date):
    date_str, time_str = get_french_datetime_strings(appointment_date)
    context = {
        **_base_context(lead),
        "jurist": jurist,
        "appointment": {
            "date": date_str,
            "time": time_str,
            "location": TDS_FRANCE_ADDRESS,
            "with_label": "Juriste",
            "with_name": _name_from_user(jurist) or "",
        },
    }
    send_html_email(
        to_email=lead.email,
        subject="Annulation de votre rendez-vous juriste – TDS France",
        template_name="email/jurist_appointment_deleted.html",
        context=context,
    )