import json, logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from api.leads.models import Lead
from api.leads.serializers import LeadSerializer

log = logging.getLogger(__name__)

def _send(event: str, instance: Lead):
    channel_layer = get_channel_layer()
    try:
        data = LeadSerializer(instance).data  # ⚠️ doit marcher hors contexte requête
    except Exception as e:
        log.exception("❌ Serializer Lead a planté dans signal: %s", e)
        data = {"id": instance.id}

    payload = {"event": event, "data": data}
    log.info("📢 [WS] send %s lead id=%s", event, instance.id)
    async_to_sync(channel_layer.group_send)(
        "leads",
        {"type": "send_event", "text": json.dumps(payload)}
    )

@receiver(post_save, sender=Lead)
def on_lead_saved(sender, instance: Lead, created, **kwargs):
    log.info("🧲 post_save Lead id=%s created=%s", instance.id, created)
    _send("created" if created else "updated", instance)

@receiver(post_delete, sender=Lead)
def on_lead_deleted(sender, instance: Lead, **kwargs):
    log.info("🧲 post_delete Lead id=%s", instance.id)
    _send("deleted", instance)