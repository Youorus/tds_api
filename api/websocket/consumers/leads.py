# api/websocket/consumers/notif.py
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

log = logging.getLogger(__name__)

class LeadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("leads", self.channel_name)
        await self.accept()
        log.info("✅ Client connecté au WS leads")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("leads", self.channel_name)
        log.info("🔌 Client déconnecté du WS leads")

    async def send_event(self, event):
        """
        Appelé par group_send — transmet l’événement au client WebSocket.
        """
        await self.send(text_data=event["text"])
