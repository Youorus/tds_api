from .base import BaseConsumer

class PaymentConsumer(BaseConsumer):
    group_prefix = "payments"

class PaymentByClientRoom(BaseConsumer):
    group_prefix = "payments-client"

    def get_group_name(self):
        client_id = int(self.scope["url_route"]["kwargs"]["client_id"])
        return f"{self.group_prefix}-{client_id}"

class PaymentByContractRoom(BaseConsumer):
    group_prefix = "payments-contract"

    def get_group_name(self):
        contract_id = int(self.scope["url_route"]["kwargs"]["contract_id"])
        return f"{self.group_prefix}-{contract_id}"