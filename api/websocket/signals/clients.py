# api/websocket/signals/clients.py
import json, logging, time
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from api.clients.models import Client
from api.clients.serializers import ClientSerializer

log = logging.getLogger(__name__)

def _broadcast(groups: list[str], payload: dict):
    layer = get_channel_layer()
    text = json.dumps(payload)
    for g in groups:
        async_to_sync(layer.group_send)(g, {"type": "send_event", "text": text})
        log.info("📢 [WS] send %s -> %s", payload.get("event"), g)

def _payload(event: str, instance: Client, changed: list[str] | None = None) -> dict:
    try:
        data = ClientSerializer(instance).data
    except Exception as e:
        log.exception("❌ ClientSerializer dans signal: %s", e)
        data = {"id": instance.id, "lead_id": instance.lead_id}
    return {
        "event": event,                 # "created" | "updated" | "deleted"
        "at": int(time.time()),         # horodatage unix
        "data": data,
        "changed": changed or [],       # champs modifiés si dispo
    }

@receiver(post_save, sender=Client)
def on_client_saved(sender, instance: Client, created, **kwargs):
    changed = list(kwargs.get("update_fields") or [])
    event = "created" if created else "updated"
    payload = _payload(event, instance, changed)

    # 🔔 Fan-out :
    # - "clients"  : tous les navigateurs écoutant les données Client (liste, fiches…)
    # - "leads"    : (optionnel) si ton UI lead doit se rafraîchir quand form_data change
    # - f"client-{instance.lead_id}" : room fine-grain (fiche client spécifique)
    groups = ["clients", f"client-{instance.lead_id}"]
    # Dé-commente si tu veux aussi toucher les écrans Leads:
    # groups.append("leads")

    # Envoie APRÈS commit pour éviter des incohérences
    transaction.on_commit(lambda: _broadcast(groups, payload))

@receiver(post_delete, sender=Client)
def on_client_deleted(sender, instance: Client, **kwargs):
    payload = _payload("deleted", instance)
    groups = ["clients", f"client-{instance.lead_id}"]
    transaction.on_commit(lambda: _broadcast(groups, payload))