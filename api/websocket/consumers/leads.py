# consumers/leads.py
from .base import BaseConsumer

class LeadConsumer(BaseConsumer):
    group_prefix = "leads"

    def get_group_name(self, **kwargs):
        if "lead_id" not in kwargs:
            self.logger.error("Missing 'lead_id' in group name resolution for LeadConsumer")
            raise ValueError("Missing 'lead_id' in group name resolution")
        return f"{self.group_prefix}_{kwargs['lead_id']}"