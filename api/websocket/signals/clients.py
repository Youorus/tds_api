# api/websocket/signals/clients.py
import logging
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from api.clients.models import Client
from api.clients.serializers import ClientSerializer
from api.websocket.signals.base import broadcast, safe_payload

log = logging.getLogger(__name__)


@receiver(post_save, sender=Client)
def on_client_saved(sender, instance: Client, created, **kwargs):
    changed = list(kwargs.get("update_fields") or [])
    if not created and not changed:
        return

    event = "created" if created else "updated"
    payload = safe_payload(event, instance, ClientSerializer, {"changed": changed})

    groups = ["clients", f"client-{instance.lead_id}"]
    transaction.on_commit(lambda: broadcast(groups, payload))


@receiver(post_delete, sender=Client)
def on_client_deleted(sender, instance: Client, **kwargs):
    if not instance.lead_id:
        return

    payload = safe_payload("deleted", instance, ClientSerializer)
    groups = ["clients", f"client-{instance.lead_id}"]
    transaction.on_commit(lambda: broadcast(groups, payload))
