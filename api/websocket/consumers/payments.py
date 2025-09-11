from .base import BaseConsumer

class PaymentConsumer(BaseConsumer):
    group_prefix = "payments"

class PaymentByClientRoom(BaseConsumer):
    group_prefix = "payments-client"

    def get_group_name(self):
        client_id = self.scope["url_route"]["kwargs"].get("client_id")
        if client_id is None:
            raise ValueError("Missing 'client_id' in URL route.")
        return f"{self.group_prefix}-{int(client_id)}"

class PaymentByContractRoom(BaseConsumer):
    group_prefix = "payments-contract"

    def get_group_name(self):
        contract_id = self.scope["url_route"]["kwargs"].get("contract_id")
        if contract_id is None:
            raise ValueError("Missing 'contract_id' in URL route.")
        return f"{self.group_prefix}-{int(contract_id)}"