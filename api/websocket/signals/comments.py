# api/websocket/signals/comments.py
import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from api.comments.models import Comment
from api.comments.serializers import CommentSerializer  # ton serializer DRF

log = logging.getLogger(__name__)


def _safe_ids(instance: Comment):
    """
    Récupère lead_id et (optionnel) client_id via lead.form_data s'il existe.
    Ton modèle Comment n'a pas de FK client, donc on le déduit du lead si possible.
    """
    # lead_id direct ou via relation
    lead_id = getattr(instance, "lead_id", None)
    if lead_id is None and getattr(instance, "lead", None):
        lead_id = getattr(instance.lead, "id", None)

    # client_id via OneToOne lead.form_data (Client), si présent
    client_id = None
    lead = getattr(instance, "lead", None)
    if lead and hasattr(lead, "form_data") and getattr(lead, "form_data", None):
        client_id = lead.form_data.id

    return lead_id, client_id


def _payload(event: str, instance: Comment):
    """
    Construit un payload JSON-sérialisable. On passe par DRF serializer,
    et on timestamp en ISO 8601. DjangoJSONEncoder gère UUID, datetime, etc.
    """
    try:
        data = CommentSerializer(instance).data
    except Exception as e:
        log.exception("❌ CommentSerializer a échoué : %s", e)
        lead_id, client_id = _safe_ids(instance)
        data = {
            "id": getattr(instance, "id", None),
            "lead_id": lead_id,
            "client_id": client_id,
            "content": getattr(instance, "content", None),
            "author": getattr(getattr(instance, "author", None), "id", None),
        }

    return {
        "event": event,  # "created" | "updated" | "deleted"
        "at": timezone.now().isoformat(),
        "data": data,
    }


def _broadcast(groups: list[str], payload: dict):
    """
    Envoie le même message sur plusieurs groupes WS.
    Utilise DjangoJSONEncoder pour rendre UUID/datetime sérialisables.
    """
    if not groups:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        log.warning("⚠️ Aucun channel layer configuré pour WebSocket")
        return
    text = json.dumps(payload, cls=DjangoJSONEncoder)
    for g in groups:
        async_to_sync(channel_layer.group_send)(g, {"type": "send_event", "text": text})
        log.info("📢 [WS] send %s -> %s", payload.get("event"), g)


@receiver(post_save, sender=Comment)
def on_comment_saved(sender, instance: Comment, created, **kwargs):
    event = "created" if created else "updated"
    payload = _payload(event, instance)
    lead_id, client_id = _safe_ids(instance)

    groups = ["comments"]
    if lead_id:
        groups.append(f"comments-lead-{lead_id}")
        groups.append("leads")  # si ta liste/KPIs leads reflètent le dernier com
    if client_id:
        groups.append(f"client-{client_id}")  # pour réveiller la fiche client liée
        groups.append("clients")

    if groups:
        transaction.on_commit(lambda: _broadcast(groups, payload))


@receiver(post_delete, sender=Comment)
def on_comment_deleted(sender, instance: Comment, **kwargs):
    payload = _payload("deleted", instance)
    lead_id, client_id = _safe_ids(instance)

    groups = ["comments"]
    if lead_id:
        groups.append(f"comments-lead-{lead_id}")
        groups.append("leads")
    if client_id:
        groups.append(f"client-{client_id}")
        groups.append("clients")

    if groups:
        transaction.on_commit(lambda: _broadcast(groups, payload))
