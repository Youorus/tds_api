# leads/routing.py
from django.urls import re_path

from api.websocket.consumers.leads import LeadConsumer

websocket_urlpatterns = [
    re_path(r"ws/leads/$", LeadConsumer.as_asgi()),
]