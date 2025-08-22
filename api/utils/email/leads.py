import os
from datetime import datetime
from urllib.parse import quote_plus

from api.utils.email.core import send_html_email
from api.utils.utils import download_file
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
    frontend_url = os.environ.get("FRONTEND_URL")
    formulaire_url = f"{frontend_url}/formulaire?id={lead.id}&name={name_param}"

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

def send_dossier_status_email(lead):
    """
    Envoie un e-mail au client lors d'un changement de statut de dossier.
    """
    if not lead.email or not lead.statut_dossier:
        # Pas d’email ou pas de statut => rien à faire
        return

    context = {
        "user": lead,  # lead doit avoir first_name, last_name, email...
        "statut_dossier": lead.statut_dossier,  # statut avec label & color
        "year": datetime.now().year,
    }

    return send_html_email(
        to_email=lead.email,
        subject=f"Votre dossier évolue – TDS France",
        template_name="email/dossier_status_update.html",
        context=context,
    )

def send_contract_email_to_lead(contract):
    client = contract.client
    lead = getattr(client, "lead", None)
    if not lead or not lead.email:
        raise ValueError("Aucun email client associé au lead.")

    # Télécharge le PDF du contrat depuis Minio ou autre storage
    pdf_content, pdf_filename = download_file(contract.contract_url)
    if not pdf_content or not pdf_filename:
        raise ValueError("Impossible de récupérer le PDF du contrat.")

    context = {
        "user": lead,
        "contract": contract,
        "year": datetime.now().year,
    }

    send_html_email(
        to_email=lead.email,
        subject="Votre contrat – TDS France",
        template_name="email/contract_send.html",
        context=context,
        attachments=[{
            "filename": pdf_filename,
            "content": pdf_content,
            "mimetype": "application/pdf"
        }]
    )


def send_receipts_email_to_lead(lead, receipts):
    """
    Envoie un ou plusieurs reçus PDF par mail au lead.
    - lead : instance Lead (doit avoir .email)
    - receipts : QuerySet/list de PaymentReceipt
    """
    if not lead or not lead.email:
        raise ValueError("Aucun email client associé au lead.")

    # Télécharge chaque PDF pour l’attacher
    attachments = []
    for receipt in receipts:
        # download_file DOIT retourner (bytes, filename)
        print(f"Téléchargement du reçu : {receipt.receipt_url}")
        pdf_content, pdf_filename = download_file(receipt.receipt_url)
        attachments.append({
            "filename": pdf_filename,
            "content": pdf_content,
            "mimetype": "application/pdf",
        })

    context = {
        "user": lead,
        "receipts": receipts,
        "year": datetime.now().year,
    }

    send_html_email(
        to_email=lead.email,
        subject="Vos reçus de paiement – TDS France",
        template_name="email/receipts_send.html",
        context=context,
        attachments=attachments,
    )