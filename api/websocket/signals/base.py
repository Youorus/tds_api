# api/websocket/signals/base.py
import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.serializers import Serializer

log = logging.getLogger(__name__)

def broadcast(groups: list[str], payload: dict):
    if not groups:
        return
    layer = get_channel_layer()
    if layer is None:
        log.warning("⚠️ Aucun channel layer configuré pour WebSocket")
        return
    text = json.dumps(payload, cls=DjangoJSONEncoder)
    for group in groups:
        async_to_sync(layer.group_send)(group, {"type": "send_event", "text": text})
        log.info("📢 [WS] send %s -> %s", payload.get("event"), group)

def safe_payload(event: str, instance, serializer_class: type[Serializer], extra_data: dict = None) -> dict:
    try:
        data = serializer_class(instance).data
    except Exception as e:
        log.exception("❌ Serializer %s a échoué : %s", serializer_class.__name__, e)
        data = {"id": getattr(instance, "id", None)}
    if extra_data:
        data.update(extra_data)
    return {
        "event": event,
        "at": instance.updated_at.isoformat() if hasattr(instance, "updated_at") else None,
        "data": data,
    }