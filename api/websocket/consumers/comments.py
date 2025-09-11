from .base import BaseConsumer
import logging

logger = logging.getLogger(__name__)

class CommentConsumer(BaseConsumer):
    group_prefix = "comments"

    def get_group_name(self):
        try:
            lead_id = self.scope["url_route"]["kwargs"]["lead_id"]
            return f"{self.group_prefix}-{lead_id}"
        except Exception as e:
            logger.error(f"❌ Erreur lors du group_name (comments) : {e}")
            return None