# api/websocket/consumers/leads.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LeadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("leads", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("leads", self.channel_name)

    async def lead_update(self, event):
        await self.send(text_data=json.dumps({
            "event": event["event"],  # "created", "updated", "deleted"
            "data": event["data"],    # le contenu du lead
        }))