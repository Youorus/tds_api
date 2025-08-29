from datetime import datetime
import logging

from api.utils.email import send_html_email
from api.utils.email.config import _build_context
from api.utils.utils import download_file

logger = logging.getLogger(__name__)


def send_contract_email_to_lead(contract):
    """
    Envoie un e-mail avec le contrat PDF en pièce jointe
    au lead associé au client, avec mise en page HTML professionnelle.

    - Utilise le template `email/contract_send.html`
    - Ajoute l’année, le contrat et les infos de contact TDS dans le contexte
    - Le PDF est téléchargé depuis l'URL du contrat (MinIO/S3/…)
    """
    client = contract.client
    lead = getattr(client, "lead", None)

    if not lead or not lead.email:
        logger.warning(f"Aucun email trouvé pour le lead du client {client}.")
        return

    # Télécharger le contrat PDF depuis son URL (MinIO/S3/etc.)
    pdf_content, pdf_filename = download_file(contract.contract_url)
    if not pdf_content or not pdf_filename:
        logger.error(f"Échec du téléchargement du contrat pour le lead {lead.id}")
        return

    # Contexte enrichi pour le template e-mail
    context = _build_context(
        lead=lead,
        extra={
            "contract": contract,
        }
    )

    # Envoi de l’e-mail
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