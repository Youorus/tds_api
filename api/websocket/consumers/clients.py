# consumers/clients.py
import logging
from .base import BaseConsumer

logger = logging.getLogger(__name__)

class ClientRoomConsumer(BaseConsumer):
    group_prefix = "client"

    def get_group_name(self):
        try:
            client_id = int(self.scope["url_route"]["kwargs"]["client_id"])
        except (KeyError, ValueError):
            raise ValueError("client_id invalide")
        try:
            return f"{self.group_prefix}-{client_id}"
        except Exception as e:
            logger.error(f"Erreur lors du group_name (client): {str(e)}")
            raise e