# consumers/leads.py
from .base import BaseConsumer

class LeadConsumer(BaseConsumer):
    group_prefix = "leads"