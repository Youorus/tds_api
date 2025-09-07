# api/websocket/consumers/leads.py

import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class LeadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("leads", self.channel_name)
        await self.accept()
        logger.info("✅ Client connecté au WebSocket 'leads' (%s)", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("leads", self.channel_name)
        logger.info("🔌 Client déconnecté du WebSocket 'leads' (%s), code: %s", self.channel_name, close_code)

    async def send_event(self, event):
        """
        Transmet un événement JSON brut reçu via group_send au client WebSocket.
        """
        try:
            await self.send(text_data=event["text"])
            logger.debug("📤 Événement envoyé au client leads: %s", event["text"])
        except Exception as e:
            logger.exception("❌ Erreur lors de l’envoi WS leads: %s", e)