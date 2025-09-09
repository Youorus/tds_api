import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from api.contracts.models import Contract
from api.contracts.serializer import ContractSerializer
from api.websocket.signals.base import safe_payload, broadcast  # ajoute cet import

log = logging.getLogger(__name__)


def _safe_ids(instance: Contract):
    client_id = getattr(instance, "client_id", None)
    if client_id is None and getattr(instance, "client", None):
        client_id = getattr(instance.client, "id", None)

    lead_id = None
    if getattr(instance, "client", None):
        lead_id = getattr(instance.client, "lead_id", None)

    return client_id, lead_id


def _payload(event: str, instance: Contract) -> dict:
    return safe_payload(event, instance, serializer_class=ContractSerializer)


@receiver(post_save, sender=Contract)
def on_contract_saved(sender, instance: Contract, created, **kwargs):
    event = "created" if created else "updated"
    payload = _payload(event, instance)
    client_id, lead_id = _safe_ids(instance)

    groups = ["contracts"]
    if client_id:
        groups.append(f"contracts-client-{client_id}")  # room par client
        groups.append(
            f"client-{client_id}"
        )  # réutilise le groupe déjà utilisé pour Client
        groups.append("clients")
    if lead_id:
        groups.append("leads")  # si tes KPIs/listes leads reflètent contrat
        groups.append(
            f"comments-lead-{lead_id}"
        )  # (optionnel) si UI coms affiche montants

    if groups:
        transaction.on_commit(lambda: broadcast(groups, payload))


@receiver(post_delete, sender=Contract)
def on_contract_deleted(sender, instance: Contract, **kwargs):
    payload = _payload("deleted", instance)
    client_id, lead_id = _safe_ids(instance)

    groups = ["contracts"]
    if client_id:
        groups.append(f"contracts-client-{client_id}")
        groups.append(f"client-{client_id}")
        groups.append("clients")
    if lead_id:
        groups.append("leads")

    if groups:
        transaction.on_commit(lambda: broadcast(groups, payload))
