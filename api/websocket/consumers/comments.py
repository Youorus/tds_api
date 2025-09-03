from channels.generic.websocket import AsyncWebsocketConsumer

GROUP = "comments"


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(GROUP, self.channel_name)
        await self.accept()
        print("✅ WS comments connecté")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])
