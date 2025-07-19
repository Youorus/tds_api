from datetime import datetime
from urllib.parse import quote_plus

from api.utils.email.core import send_html_email
from tds import settings


def send_lead_assignment_request_to_admin(conseiller, lead):
    context = {
        "conseiller": conseiller,
        "lead": lead,
    }
    send_html_email(
        to_email="admin@tds-france.fr",  # ou boucle sur tous les admins
        subject=f"Demande d'assignation d'un lead : {lead}",
        template_name="email/lead_assignment_request.html",
        context=context,
    )

def send_lead_assignment_confirmation_to_conseiller(conseiller, lead):
    context = {
        "conseiller": conseiller,
        "lead": lead,
    }
    send_html_email(
        to_email=conseiller.email,
        subject="Votre demande d'assignation a été validée",
        template_name="email/lead_assignment_confirm.html",
        context=context,
    )

def send_formulaire_email(self, lead):
    # Encode le nom proprement dans l’URL
    name_param = quote_plus(f"{lead.first_name} {lead.last_name}")
    formulaire_url = f"{settings.FRONTEND_BASE_URL}/formulaire?id={lead.id}&name={name_param}"

    context = {
        "user": lead,
        "formulaire_url": formulaire_url,
        "year": datetime.now().year,
    }

    # Vérifie qu’il y a un email, sinon fail silencieusement ou log
    if not lead.email:
        print(f"[WARNING] Aucun email pour le lead {lead.id}")
        return

    return send_html_email(
        to_email=lead.email,
        subject="Merci de compléter votre formulaire – TDS France",
        template_name="email/formulaire_link.html",
        context=context,
    )