from datetime import timedelta
from django.utils import timezone
from celery import shared_task
import logging

from api.payments.models import PaymentReceipt
from api.utils.email.recus.notifications import send_payment_due_email

logger = logging.getLogger(__name__)

"""
Tâche périodique pour envoyer des e-mails de rappel aux clients :
- 3 jours avant l’échéance (J-3)
- 1 jour avant l’échéance (J-1)
"""


@shared_task
def send_payment_due_reminders():
    today = timezone.localdate()
    in_1_day = today + timedelta(days=1)
    in_3_days = today + timedelta(days=3)

    # 💡 Filtre les reçus dont l'échéance est dans 1 ou 3 jours
    receipts = PaymentReceipt.objects.filter(
        next_due_date__in=[in_3_day, in_1_day]
    ).select_related("client", "contract")

    for receipt in receipts:
        client = receipt.client
        email = getattr(client.lead, "email", None)

        if not email:
            logger.warning(f"⚠️ Aucun email pour le client #{client.id} - impossible d’envoyer un rappel.")
            continue

        try:
            # 💸 Reste à payer = montant total - déjà versé
            amount_due = receipt.contract.amount - receipt.contract.total_paid

            send_payment_due_email(
                client=client,
                receipt=receipt,
                due_date=receipt.next_due_date,
                amount=amount_due
            )
            logger.info(
                f"📧 Rappel de paiement envoyé à {email} (client #{client.id}, échéance le {receipt.next_due_date})")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l’envoi du mail de rappel pour le client #{client.id} : {str(e)}")