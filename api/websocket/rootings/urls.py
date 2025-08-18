# leads/routing.py
from django.urls import re_path

from api.websocket.consumers.clients import ClientRoomConsumer
from api.websocket.consumers.comments import CommentConsumer
from api.websocket.consumers.leads import LeadConsumer

websocket_urlpatterns = [
    re_path(r"ws/leads/$", LeadConsumer.as_asgi()),
    re_path(r"^ws/client/(?P<lead_id>\d+)/$", ClientRoomConsumer.as_asgi()),
    re_path(r"^ws/comments/$", CommentConsumer.as_asgi()), # optionnel
]