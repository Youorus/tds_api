# leads/routing.py (ou api/websocket/rootings/urls.py)

from django.urls import re_path
from api.websocket.consumers.leads import LeadConsumer
from api.websocket.consumers.clients import ClientRoomConsumer

websocket_urlpatterns = [
    re_path(r"^ws/leads/$", LeadConsumer.as_asgi()),  # ✅ Route globale
    re_path(r"^ws/leads/(?P<lead_id>\d+)/?$", LeadConsumer.as_asgi()),  # optionnel si besoin
    re_path(r"^ws/clients/(?P<client_id>\d+)/?$", ClientRoomConsumer.as_asgi()),
]