# leads/tests/test_send_emai.py

import pytest
from api.services import NotificationService
from unittest.mock import MagicMock

def test_send_appointment_confirmation_calls_email(monkeypatch):
    """
    Vérifie que la notification de confirmation envoie un email.
    """
    service = NotificationService()
    # Mock la fonction d’envoi réel d’email
    service._send_email = MagicMock()
    dummy_lead = MagicMock(email="test@example.com")
    service.send_appointment_confirmation(dummy_lead)
    service._send_email.assert_called()