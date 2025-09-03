# api/websocket/consumers/client_room.py
from channels.generic.websocket import AsyncWebsocketConsumer


class ClientRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # /ws/client/<lead_id>/
        self.lead_id = self.scope["url_route"]["kwargs"]["lead_id"]
        self.group = f"client-{self.lead_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        print(f"✅ WS client-room join {self.group}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])
