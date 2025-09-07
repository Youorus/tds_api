# api/websocket/signals/payments.py
import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from api.payments.models import PaymentReceipt
from api.payments.serializers import PaymentReceiptSerializer

log = logging.getLogger(__name__)


def _safe_ids(instance: PaymentReceipt):
    client_id = getattr(instance, "client_id", None)
    if client_id is None and getattr(instance, "client", None):
        client_id = getattr(instance.client, "id", None)

    contract_id = getattr(instance, "contract_id", None)
    if contract_id is None and getattr(instance, "contract", None):
        contract_id = getattr(instance.contract, "id", None)

    lead_id = None
    try:
        if getattr(instance, "client", None):
            lead_id = getattr(instance.client, "lead_id", None)
    except Exception:
        lead_id = None

    return client_id, contract_id, lead_id


def _payload(event: str, instance: PaymentReceipt) -> dict:
    try:
        data = PaymentReceiptSerializer(instance).data
    except Exception:
        client_id, contract_id, lead_id = _safe_ids(instance)
        data = {
            "id": getattr(instance, "id", None),
            "client_id": client_id,
            "contract_id": contract_id,
            "lead_id": lead_id,
            "amount": str(getattr(instance, "amount", "")),
            "mode": getattr(instance, "mode", None),
            "payment_date": getattr(instance, "payment_date", None),
            "next_due_date": getattr(instance, "next_due_date", None),
            "receipt_url": getattr(instance, "receipt_url", None),
            "created_by": getattr(getattr(instance, "created_by", None), "id", None),
        }
    return {
        "event": event,
        "at": timezone.now().isoformat(),
        "data": data,
    }


def _broadcast(groups: list[str], payload: dict):
    layer = get_channel_layer()
    if not layer:
        log.warning("❌ Channel layer non disponible")
        return
    if not groups:
        return

    text = json.dumps(payload, cls=DjangoJSONEncoder)  # gère UUID/Decimal/datetime
    for g in groups:
        async_to_sync(layer.group_send)(g, {"type": "send_event", "text": text})
        log.info("📢 [WS] send %s -> %s", payload.get("event"), g)


@receiver(post_save, sender=PaymentReceipt)
def on_payment_saved(sender, instance: PaymentReceipt, created, **kwargs):
    event = "created" if created else "updated"
    payload = _payload(event, instance)
    client_id, contract_id, lead_id = _safe_ids(instance)

    groups = ["payments"]
    if client_id is not None:
        groups += [f"payments-client-{client_id}", f"client-{client_id}", "clients"]
        # Réveiller les contrats liés au client (soldes etc.)
        groups += [f"contracts-client-{client_id}", "contracts"]
    if contract_id is not None:
        groups += [f"payments-contract-{contract_id}"]
    if lead_id is not None:
        groups += ["leads"]

    transaction.on_commit(lambda: _broadcast(groups, payload))


@receiver(post_delete, sender=PaymentReceipt)
def on_payment_deleted(sender, instance: PaymentReceipt, **kwargs):
    payload = _payload("deleted", instance)
    client_id, contract_id, lead_id = _safe_ids(instance)

    groups = ["payments"]
    if client_id is not None:
        groups += [
            f"payments-client-{client_id}",
            f"client-{client_id}",
            "clients",
            f"contracts-client-{client_id}",
            "contracts",
        ]
    if contract_id is not None:
        groups += [f"payments-contract-{contract_id}"]
    if lead_id is not None:
        groups += ["leads"]

    transaction.on_commit(lambda: _broadcast(groups, payload))
