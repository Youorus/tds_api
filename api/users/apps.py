# api/users/apps.py

from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api.users"

    def ready(self):
        import api.websocket.signals.leads
        import api.websocket.signals.clients
        import api.websocket.signals.comments
        import api.websocket.signals.contracts
        import api.websocket.signals.payments