from api.utils.email.core import send_html_email

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