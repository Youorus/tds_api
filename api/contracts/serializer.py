from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from api.clients.serializers import ClientSerializer
from api.contracts.models import Contract
from api.services.serializers import ServiceSerializer


class ContractSerializer(serializers.ModelSerializer):
    amount_paid = serializers.SerializerMethodField()
    real_amount_due = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    # Ces deux lignes : version lecture seule pour l’affichage
    client_details = ClientSerializer(source="client", read_only=True)
    service_details = ServiceSerializer(source="service", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "client",           # ← ID du client (clé étrangère) accepté à la création
            "client_details",   # ← Détail complet, lecture seule
            "service",          # ← ID du service (clé étrangère)
            "service_details",  # ← Détail complet, lecture seule
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
            "client_details",
            "service_details",
        ]

    def get_amount_paid(self, obj):
        return sum(receipt.amount for receipt in obj.receipts.all())

    def get_real_amount_due(self, obj):
        ratio = Decimal("1.00") - (obj.discount_percent or Decimal("0.00")) / Decimal("100.00")
        return (obj.amount_due * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_is_fully_paid(self, obj):
        return self.get_amount_paid(obj) >= self.get_real_amount_due(obj)