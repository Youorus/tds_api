# api/websocket/consumers/payments.py
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
logger = logging.getLogger(__name__)


class PaymentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("payments", self.channel_name)
        await self.accept()
        logger.info("✅ WS payments connecté")

    async def disconnect(self, code):
        await self.channel_layer.group_discard("payments", self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])


class PaymentByClientRoom(AsyncWebsocketConsumer):
    async def connect(self):
        # /ws/payments/client/<client_id>/
        self.client_id = self.scope["url_route"]["kwargs"]["client_id"]
        self.group = f"payments-client-{self.client_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.info(f"✅ WS payments room {self.group}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])


class PaymentByContractRoom(AsyncWebsocketConsumer):
    async def connect(self):
        # /ws/payments/contract/<contract_id>/
        self.contract_id = self.scope["url_route"]["kwargs"]["contract_id"]
        self.group = f"payments-contract-{self.contract_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.info(f"✅ WS payments room {self.group}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def send_event(self, event):
        await self.send(text_data=event["text"])
