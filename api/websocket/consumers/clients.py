# consumers/clients.py
from .base import BaseConsumer

class ClientRoomConsumer(BaseConsumer):
    group_prefix = "client"

    def get_group_name(self):
        try:
            client_id = int(self.scope["url_route"]["kwargs"]["client_id"])
        except (KeyError, ValueError):
            raise ValueError("client_id invalide")
        return f"{self.group_prefix}-{client_id}"