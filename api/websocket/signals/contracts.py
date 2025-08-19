import json
import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from api.contracts.models import Contract
from api.contracts.serializer import ContractSerializer

log = logging.getLogger(__name__)

def _safe_ids(instance: Contract):
    client_id = getattr(instance, "client_id", None)
    if client_id is None and getattr(instance, "client", None):
        client_id = getattr(instance.client, "id", None)

    # via Client → Lead (OneToOne)
    lead_id = None
    try:
        if getattr(instance, "client", None):
            lead_id = getattr(instance.client, "lead_id", None)
    except Exception:
        lead_id = None

    return client_id, lead_id

def _payload(event: str, instance: Contract) -> dict:
    try:
        data = ContractSerializer(instance).data
    except Exception as e:
        log.exception("❌ ContractSerializer a échoué : %s", e)
        client_id, lead_id = _safe_ids(instance)
        data = {
            "id": getattr(instance, "id", None),
            "client_id": client_id,
            "lead_id": lead_id,
            "amount_due": str(getattr(instance, "amount_due", "")),
            "discount_percent": str(getattr(instance, "discount_percent", "")),
            "is_signed": getattr(instance, "is_signed", False),
            "is_refunded": getattr(instance, "is_refunded", False),
            "refund_amount": str(getattr(instance, "refund_amount", "0.00")),
            "contract_url": getattr(instance, "contract_url", None),
            "created_at": getattr(instance, "created_at", None),
        }

    return {
        "event": event,                        # "created" | "updated" | "deleted"
        "at": timezone.now().isoformat(),
        "data": data,
    }

def _broadcast(groups: list[str], payload: dict):
    layer = get_channel_layer()
    text = json.dumps(payload, cls=DjangoJSONEncoder)  # UUID/datetime/Decimal safe
    for g in groups:
        async_to_sync(layer.group_send)(g, {"type": "send_event", "text": text})
        log.info("📢 [WS] send %s -> %s", payload.get("event"), g)

@receiver(post_save, sender=Contract)
def on_contract_saved(sender, instance: Contract, created, **kwargs):
    event = "created" if created else "updated"
    payload = _payload(event, instance)
    client_id, lead_id = _safe_ids(instance)

    groups = ["contracts"]
    if client_id is not None:
        groups.append(f"contracts-client-{client_id}")  # room par client
        groups.append(f"client-{client_id}")            # réutilise le groupe déjà utilisé pour Client
        groups.append("clients")
    if lead_id is not None:
        groups.append("leads")                          # si tes KPIs/listes leads reflètent contrat
        groups.append(f"comments-lead-{lead_id}")       # (optionnel) si UI coms affiche montants

    transaction.on_commit(lambda: _broadcast(groups, payload))

@receiver(post_delete, sender=Contract)
def on_contract_deleted(sender, instance: Contract, **kwargs):
    payload = _payload("deleted", instance)
    client_id, lead_id = _safe_ids(instance)

    groups = ["contracts"]
    if client_id is not None:
        groups.append(f"contracts-client-{client_id}")
        groups.append(f"client-{client_id}")
        groups.append("clients")
    if lead_id is not None:
        groups.append("leads")

    transaction.on_commit(lambda: _broadcast(groups, payload))