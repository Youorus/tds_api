from decimal import Decimal

from rest_framework import serializers
from api.models import PaymentReceipt
from api.models.PaymentReceipt import PaymentMode


class PaymentReceiptSerializer(serializers.ModelSerializer):
    contract_id = serializers.IntegerField(source="contract.id", read_only=True)
    contract_service = serializers.CharField(source="contract.service", read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            "id",
            "contract_id",
            "client",
            "contract",
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
            "receipt_url",  # OK car géré par generate_pdf
            "created_by",  # OK car set par perform_create
        ]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Le montant doit être supérieur à zéro.")
        return value

    def validate_mode(self, value):
        if value not in PaymentMode.values:
            raise serializers.ValidationError("Mode de paiement invalide.")
        return value