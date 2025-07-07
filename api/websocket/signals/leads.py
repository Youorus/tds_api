# api/signals/lead_signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from api.leads.models import Lead
from api.leads.serializers import LeadSerializer


@receiver(post_save, sender=Lead)
def lead_updated_or_created(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    data = LeadSerializer(instance).data
    event_type = "created" if created else "updated"

    async_to_sync(channel_layer.group_send)(
        "leads",  # groupe auquel les clients sont abonnés
        {
            "type": "lead_update",
            "event": event_type,
            "data": data,
        }
    )