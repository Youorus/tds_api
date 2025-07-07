from decimal import Decimal
from rest_framework import serializers

from api.payments.enums import PaymentMode
from api.payments.models import PaymentReceipt


class PaymentReceiptSerializer(serializers.ModelSerializer):
    contract_id = serializers.IntegerField(source="contract.id", read_only=True)
    contract_service = serializers.CharField(source="contract.service", read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            "id",
            "client",
            "contract",
            "contract_id",
            "contract_service",
            "mode",
            "payment_date",
            "receipt_url",
            "amount",
            "created_by",
            "next_due_date",
        ]
        read_only_fields = [
            "id",
            "contract_id",
            "contract_service",
            "receipt_url",
            "created_by",
        ]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value

    def validate_mode(self, value):
        if value not in PaymentMode.values:
            raise serializers.ValidationError("Mode de paiement invalide.")
        return value