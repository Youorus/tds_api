# leads/routing.py
from django.urls import re_path

from api.websocket.consumers.clients import ClientRoomConsumer
from api.websocket.consumers.comments import CommentConsumer
from api.websocket.consumers.contracts import ContractByClientRoom, ContractConsumer
from api.websocket.consumers.leads import LeadConsumer
from api.websocket.consumers.payments import (
    PaymentByClientRoom,
    PaymentByContractRoom,
    PaymentConsumer,
)

websocket_urlpatterns = [
    re_path(r"ws/leads/$", LeadConsumer.as_asgi()),
    re_path(r"^ws/client/(?P<lead_id>\d+)/$", ClientRoomConsumer.as_asgi()),
    re_path(r"^ws/comments/$", CommentConsumer.as_asgi()),
    re_path(r"^ws/contracts/$", ContractConsumer.as_asgi()),
    re_path(
        r"^ws/contracts/client/(?P<client_id>\d+)/$", ContractByClientRoom.as_asgi()
    ),
    re_path(r"^ws/payments/$", PaymentConsumer.as_asgi()),
    re_path(r"^ws/payments/client/(?P<client_id>\d+)/$", PaymentByClientRoom.as_asgi()),
    re_path(
        r"^ws/payments/contract/(?P<contract_id>\d+)/$", PaymentByContractRoom.as_asgi()
    ),
]
