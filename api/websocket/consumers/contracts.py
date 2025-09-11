from .base import BaseConsumer

class ContractConsumer(BaseConsumer):
    group_prefix = "contracts"

class ContractByClientRoom(BaseConsumer):
    group_prefix = "contracts-client"

    def get_group_name(self):
        try:
            client_id = int(self.scope["url_route"]["kwargs"]["client_id"])
            return f"{self.group_prefix}-{client_id}"
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Erreur de group_name (contracts-client): {e}")
            raise Exception("client_id manquant ou invalide dans l'URL.")