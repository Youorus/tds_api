# consumers/base.py

import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)


class BaseConsumer(AsyncWebsocketConsumer):
    group_prefix = None  # À override dans les subclasses

    async def connect(self):
        self.group = None

        if not self.channel_layer:
            logger.warning(f"❌ Channel layer non disponible ({self.group_prefix})")
            await self.close()
            return

        try:
            # ✅ Récupération des kwargs depuis le scope
            self.group = self.get_group_name(**self.scope.get("url_route", {}).get("kwargs", {}))
            await self.channel_layer.group_add(self.group, self.channel_name)
            await self.accept()
            logger.info(f"✅ WS connecté au groupe {self.group}")
        except ResponseError as e:
            logger.error(f"❌ Limite Redis atteinte pour le groupe {self.group_prefix} : {e}")
            await self.close()
        except Exception as e:
            logger.error(f"❌ Erreur lors du group_name ({self.group_prefix}) : {e}")
            await self.close()

    async def disconnect(self, code):
        if self.group:
            await self.channel_layer.group_discard(self.group, self.channel_name)
            logger.info(f"🔌 Déconnecté du groupe {self.group}")
        else:
            logger.warning("⚠️ Aucune déconnexion car aucun groupe assigné")

    async def send_event(self, event):
        try:
            await self.send(text_data=event["text"])
        except Exception as e:
            logger.exception(f"❌ Erreur d'envoi WS ({self.group}): {e}")

    def get_group_name(self, **kwargs) -> str:
        if not self.group_prefix:
            raise ValueError("group_prefix manquant")
        return self.group_prefix