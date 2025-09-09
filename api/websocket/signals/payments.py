# api/websocket/signals/payments.py
import logging
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from api.payments.models import PaymentReceipt
from api.payments.serializers import PaymentReceiptSerializer
from api.websocket.signals.base import broadcast, safe_payload

log = logging.getLogger(__name__)


def _safe_ids(instance: PaymentReceipt):
    client_id = getattr(instance, "client_id", None)
    if client_id is None and getattr(instance, "client", None):
        client_id = getattr(instance.client, "id", None)

    contract_id = getattr(instance, "contract_id", None)
    if contract_id is None and getattr(instance, "contract", None):
        contract_id = getattr(instance.contract, "id", None)

    lead_id = getattr(instance.client, "lead_id", None) if getattr(instance, "client", None) else None

    return client_id, contract_id, lead_id


@receiver(post_save, sender=PaymentReceipt)
def on_payment_saved(sender, instance: PaymentReceipt, created, **kwargs):
    event = "created" if created else "updated"
    client_id, contract_id, lead_id = _safe_ids(instance)

    extra_data = {
        "client_id": client_id,
        "contract_id": contract_id,
        "lead_id": lead_id,
    }

    payload = safe_payload(event, instance, PaymentReceiptSerializer, extra_data=extra_data)

    groups = ["payments"]
    if client_id:
        groups += [f"payments-client-{client_id}", f"client-{client_id}", "clients", f"contracts-client-{client_id}", "contracts"]
    if contract_id:
        groups += [f"payments-contract-{contract_id}"]
    if lead_id:
        groups += ["leads"]

    transaction.on_commit(lambda: broadcast(groups, payload))


@receiver(post_delete, sender=PaymentReceipt)
def on_payment_deleted(sender, instance: PaymentReceipt, **kwargs):
    client_id, contract_id, lead_id = _safe_ids(instance)

    extra_data = {
        "client_id": client_id,
        "contract_id": contract_id,
        "lead_id": lead_id,
    }

    payload = safe_payload("deleted", instance, PaymentReceiptSerializer, extra_data=extra_data)

    groups = ["payments"]
    if client_id:
        groups += [f"payments-client-{client_id}", f"client-{client_id}", "clients", f"contracts-client-{client_id}", "contracts"]
    if contract_id:
        groups += [f"payments-contract-{contract_id}"]
    if lead_id:
        groups += ["leads"]

    transaction.on_commit(lambda: broadcast(groups, payload))