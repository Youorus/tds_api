# api/websocket/consumers/contracts.py
from channels.generic.websocket import AsyncWebsocketConsumer

class ContractConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("contracts", self.channel_name)
        await self.accept()
        print("✅ WS contracts connecté")

    async def disconnect(self, code):
        await self.channel_layer.group_discard("contracts", self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])


class ContractByClientRoom(AsyncWebsocketConsumer):
    async def connect(self):
        # /ws/contracts/client/<client_id>/
        self.client_id = self.scope["url_route"]["kwargs"]["client_id"]
        self.group = f"contracts-client-{self.client_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        print(f"✅ WS contracts room {self.group}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])