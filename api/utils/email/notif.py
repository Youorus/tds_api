import os
from datetime import datetime
from urllib.parse import quote_plus

from api.utils.email import send_html_email
from api.utils.utils import download_file
from tds import settings




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