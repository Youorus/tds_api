# api/leads/signals.py

import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from api.leads.models import Lead
from api.leads.serializers import LeadSerializer

log = logging.getLogger(__name__)


def _send(event: str, instance: Lead):
    channel_layer = get_channel_layer()
    if not channel_layer:
        log.warning("❌ Channel layer non disponible")
        return

    try:
        data = LeadSerializer(instance).data
    except Exception:
        data = {"id": instance.id}

    payload = {"event": event, "data": data}
    log.info("📢 [WS] Envoi event '%s' pour lead id=%s", event, instance.id)

    async_to_sync(channel_layer.group_send)(
        "leads",
        {
            "type": "send_event",
            "text": json.dumps(payload),
        }
    )


@receiver(post_save, sender=Lead)
def on_lead_saved(sender, instance: Lead, created, **kwargs):
    log.info("🧲 post_save Lead id=%s (created=%s)", instance.id, created)
    _send("created" if created else "updated", instance)


@receiver(post_delete, sender=Lead)
def on_lead_deleted(sender, instance: Lead, **kwargs):
    log.info("🧲 post_delete Lead id=%s", instance.id)
    _send("deleted", instance)