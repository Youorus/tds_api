from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_contract_email_task(contract_id: int):
    """
    Task Celery pour envoyer un contrat par e-mail au lead associé.
    """
    from api.contracts.models import Contract  # Import local pour éviter les imports circulaires
    from api.utils.email.contracts.notifications import send_contract_email_to_lead

    contract = Contract.objects.select_related("client__lead").filter(id=contract_id).first()

    if contract and contract.client and contract.client.lead and contract.client.lead.email:
        send_contract_email_to_lead(contract)
        logger.info(f"📩 Contrat #{contract.id} envoyé à {contract.client.lead.email}")
    else:
        logger.warning(f"❌ Contrat #{contract_id} non envoyé – données incomplètes (lead ou email manquant)")