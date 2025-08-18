# tds/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from api.websocket.rootings.urls import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")

print("🚀 Chargement ASGI tds.asgi.application")  # <— DOIT s'afficher au boot

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})