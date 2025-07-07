from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from api.contracts.models import Contract


class ContractSerializer(serializers.ModelSerializer):
    amount_paid = serializers.SerializerMethodField()
    real_amount_due = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "client",
            "service",
            "amount_due",
            "discount_percent",
            "real_amount_due",
            "amount_paid",
            "is_fully_paid",
            "contract_url",
            "created_at",
            "is_signed",
            "created_by"
        ]
        read_only_fields = [
            "id",
            "real_amount_due",
            "amount_paid",
            "is_fully_paid",
            "contract_url",
            "created_at",
            "created_by",
        ]

    def get_amount_paid(self, obj):
        return sum(receipt.amount for receipt in obj.receipts.all())

    def get_real_amount_due(self, obj):
        ratio = Decimal("1.00") - (obj.discount_percent or Decimal("0.00")) / Decimal("100.00")
        return (obj.amount_due * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_is_fully_paid(self, obj):
        return self.get_amount_paid(obj) >= self.get_real_amount_due(obj)