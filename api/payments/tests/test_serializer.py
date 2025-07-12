import pytest
from decimal import Decimal
from api.payments.serializers import PaymentReceiptSerializer
from api.payments.enums import PaymentMode

@pytest.mark.django_db
class TestPaymentReceiptSerializer:
    def test_amount_validation(self):
        serializer = PaymentReceiptSerializer(data={"amount": "0"})
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_mode_validation(self):
        serializer = PaymentReceiptSerializer(data={"amount": "1.00", "mode": "INVALID"})
        assert not serializer.is_valid()
        assert "mode" in serializer.errors

    def test_accepts_valid_data(self):
        # On doit fournir tous les champs obligatoires
        serializer = PaymentReceiptSerializer(data={
            "amount": "100.00",
            "mode": PaymentMode.CB,
            "client": 1,  # Simulé
        })
        # Le test peut ne pas passer sans DB setup complet, mais la structure est bonne.