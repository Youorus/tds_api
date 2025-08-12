# api/contracts/serializer.py

from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from api.contracts.models import Contract
from api.clients.serializers import ClientSerializer
from api.services.serializers import ServiceSerializer

class ContractSerializer(serializers.ModelSerializer):
    amount_paid = serializers.SerializerMethodField()
    real_amount_due = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    # ⇩⇩⇩ nouveaux champs exposés depuis les @property du modèle
    balance_due = serializers.SerializerMethodField()
    net_paid = serializers.SerializerMethodField()

    client_details = ClientSerializer(source="client", read_only=True)
    service_details = ServiceSerializer(source="service", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "client",
            "client_details",
            "service",
            "service_details",
            "amount_due",
            "discount_percent",
            "real_amount_due",
            "amount_paid",
            "net_paid",        # ⇦ nouveau
            "balance_due",     # ⇦ nouveau
            "is_fully_paid",
            "is_refunded",
            "refund_amount",
            "contract_url",
            "created_at",
            "is_signed",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "real_amount_due",
            "amount_paid",
            "net_paid",
            "balance_due",
            "is_fully_paid",
            "contract_url",
            "created_at",
            "created_by",
            "client_details",
            "service_details",
            "is_refunded",
            "refund_amount",
        ]

    def get_amount_paid(self, obj):
        return float(obj.amount_paid)  # ou str si tu préfères

    def get_real_amount_due(self, obj):
        ratio = Decimal("1.00") - (obj.discount_percent or Decimal("0.00")) / Decimal("100.00")
        return float((obj.amount_due * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def get_is_fully_paid(self, obj):
        return obj.is_fully_paid

    def get_balance_due(self, obj):
        return float(obj.balance_due)

    def get_net_paid(self, obj):
        return float(obj.net_paid)