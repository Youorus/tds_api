# api/signals/lead_signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from api.leads.models import Lead
from api.leads.serializers import LeadSerializer

@receiver(post_save, sender=Lead)
def lead_created_or_updated(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    data = LeadSerializer(instance).data
    event_type = "created" if created else "updated"

    async_to_sync(channel_layer.group_send)(
        "leads",
        {
            "type": "lead_update",
            "event": event_type,
            "data": data,
        }
    )

@receiver(post_delete, sender=Lead)
def lead_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        "leads",
        {
            "type": "lead_update",
            "event": "deleted",
            "data": {"id": instance.id},  # ⚠️ pas de serializer ici, objet supprimé
        }
    )