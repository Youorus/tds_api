import logging

from api.utils.cloud.scw.utils import download_file_from_s3, extract_s3_key_from_url
from api.utils.email import send_html_email
from api.utils.email.config import _build_context

logger = logging.getLogger(__name__)


def send_contract_email_to_lead(contract):
    """
    Envoie un e-mail avec le contrat PDF en pièce jointe
    au lead associé au client, avec mise en page HTML professionnelle.

    - Utilise le template `email/contract_send.html`
    - Le contrat PDF est téléchargé depuis Scaleway S3 (bucket privé)
    """
    client = contract.client
    lead = getattr(client, "lead", None)

    if not lead or not lead.email:
        logger.warning(f"Aucun email trouvé pour le lead du client {client}.")
        return

    key = contract.contract_url

    try:
        key = extract_s3_key_from_url(key)
        pdf_content, pdf_filename = download_file_from_s3("contracts", key)
    except Exception as e:
        logger.error(f"Échec du téléchargement du contrat pour lead {lead.id} : {e}")
        return

    # Contexte enrichi pour le template email
    context = _build_context(lead=lead, extra={"contract": contract})

    # Envoi de l’e-mail avec pièce jointe
    send_html_email(
        to_email=lead.email,
        subject="Votre contrat – TDS France",
        template_name="email/contract/contract_send.html",
        context=context,
        attachments=[
            {
                "filename": pdf_filename,
                "content": pdf_content,
                "mimetype": "application/pdf",
            }
        ],
    )

    logger.info(f"📩 Contrat #{contract.id} envoyé à {lead.email}")
