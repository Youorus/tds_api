from .base import BaseConsumer

class ContractConsumer(BaseConsumer):
    group_prefix = "contracts"

class ContractByClientRoom(BaseConsumer):
    group_prefix = "contracts-client"

    def get_group_name(self):
        client_id = int(self.scope["url_route"]["kwargs"]["client_id"])
        return f"{self.group_prefix}-{client_id}"