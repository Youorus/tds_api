# api/websocket/consumers/notif.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class LeadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("leads", self.channel_name)
        await self.accept()
        print("✅ Client connecté au WS leads")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("leads", self.channel_name)

    async def send_event(self, event):
        """
        Méthode appelée par group_send.
        """
        await self.send(text_data=event["text"])
