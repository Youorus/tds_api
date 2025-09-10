# api/websocket/signals/comments.py
import logging
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from api.comments.models import Comment
from api.comments.serializers import CommentSerializer
from api.websocket.signals.base import broadcast, safe_payload

log = logging.getLogger(__name__)


def _safe_ids(instance: Comment, event: str = "deleted"):
    return safe_payload(event, instance, CommentSerializer)


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
        "event": event,
        "at": timezone.now().isoformat(),
        "data": data,
    }


def _broadcast(groups: list[str], payload: dict):
    broadcast(groups, payload)


@receiver(post_save, sender=Comment)
def on_comment_saved(sender, instance: Comment, created, **kwargs):
    event = "created" if created else "updated"
    payload = _payload(event, instance)
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