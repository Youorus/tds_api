from datetime import datetime
import logging

from api.utils.email import send_html_email
from api.utils.email.config import _build_context
from api.utils.utils import download_file

logger = logging.getLogger(__name__)

def send_receipts_email_to_lead(lead, receipts):
    """
    Envoie un ou plusieurs reçus PDF par mail au lead associé à un client.

    - Utilise le template `email/receipts_send.html`
    - Ajoute l’année et les reçus dans le contexte
    - Chaque reçu PDF est téléchargé depuis son URL
    """
    if not lead or not lead.email:
        logger.warning(f"Aucun email trouvé pour le lead.")
        return

    attachments = []
    for receipt in receipts:
        logger.info(f"Téléchargement du reçu : {receipt.receipt_url}")
        pdf_content, pdf_filename = download_file(receipt.receipt_url)
        if not pdf_content or not pdf_filename:
            logger.error(f"Échec du téléchargement du reçu {receipt.id}")
            continue

        attachments.append({
            "filename": pdf_filename,
            "content": pdf_content,
            "mimetype": "application/pdf",
        })

    if not attachments:
        logger.warning(f"Aucune pièce jointe valide pour {lead}.")
        return

    context = _build_context(
        lead=lead,
        extra={
            "receipts": receipts,
        }
    )

    send_html_email(
        to_email=lead.email,
        subject="Vos reçus de paiement – TDS France",
        template_name="email/recus/receipts_send.html",
        context=context,
        attachments=attachments,
    )

def send_payment_due_email(client, receipt, due_date, amount):
    """
    Envoie un rappel par email concernant un paiement à venir.

    - Utilise le template HTML : `email/payment_due.html`
    - Ajoute dans le contexte : client, reçu, date d’échéance, montant
    - Envoie à client.email ou lead.email
    """
    recipient = client.lead.email
    if not recipient:
        return

    context = _build_context(
        lead=client.lead,
        extra={
            "client": client,
            "receipt": receipt,
            "due_date": due_date.strftime("%d/%m/%Y"),
            "amount": f"{amount:.2f}€",
        },
    )

    subject = "Rappel : Échéance de paiement"
    send_html_email(
        to_email=recipient,
        subject=subject,
        template_name="email/recus/payment_reminder.html",
        context=context,
    )