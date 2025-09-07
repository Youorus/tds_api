# api/websocket/consumers/client_room.py
# api/websocket/consumers/client_room.py
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class ClientRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lead_id = self.scope["url_route"]["kwargs"]["lead_id"]
        self.group = f"client-{self.lead_id}"

        if self.channel_layer is None:
            logger.warning("❌ Channel layer not available during connect")
            await self.close()
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.info(f"✅ WS client-room joined {self.group}")

    async def disconnect(self, code):
        if self.channel_layer:
            await self.channel_layer.group_discard(self.group, self.channel_name)
            logger.info(f"👋 WS client-room left {self.group} (code={code})")

    async def send_event(self, event):
        try:
            await self.send(text_data=event["text"])
        except Exception as e:
            logger.exception(f"❌ Error sending WS event to {self.group}: {e}")
