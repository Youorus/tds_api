import logging

from celery import shared_task

from api.utils.email.recus.notifications import send_receipts_email_to_lead

logger = logging.getLogger(__name__)


@shared_task
def send_receipts_email_task(lead_id: int):
    """
    Task Celery pour envoyer les reçus de paiement par e-mail au lead associé.
    """
    from api.leads.models import (
        Lead,
    )  # Import local pour éviter les imports circulaires
    from api.payments.models import PaymentReceipt

    lead = Lead.objects.filter(id=lead_id).first()

    if not lead or not lead.email:
        logger.warning(
            f"❌ Reçus non envoyés – lead #{lead_id} introuvable ou sans email."
        )
        return

    receipts = PaymentReceipt.objects.filter(client__lead=lead).exclude(
        receipt_url__isnull=True
    )

    if not receipts.exists():
        logger.warning(
            f"❌ Aucun reçu à envoyer pour le lead #{lead_id} ({lead.email})."
        )
        return

    send_receipts_email_to_lead(lead, receipts)
    logger.info(f"📩 {receipts.count()} reçu(s) envoyé(s) à {lead.email}")
