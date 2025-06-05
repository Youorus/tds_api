from rest_framework import serializers
from api.models import Payment, PaymentReceipt


class PaymentReceiptSerializer(serializers.ModelSerializer):
    service = serializers.CharField(source="plan.service", read_only=True)
    client_name = serializers.CharField(source="client.full_name", read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            "id", "client", "client_name", "plan", "amount", "mode",
            "payment_date", "receipt_url", "service", "created_by"
        ]
        read_only_fields = [
            "id", "created_by", "payment_date", "receipt_url", "service", "client_name"
        ]
        extra_kwargs = {
            "client": {"required": False},
            "plan": {"required": False},
        }


class PaymentSerializer(serializers.ModelSerializer):
    receipts = PaymentReceiptSerializer(many=True, read_only=True)
    real_amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_fully_paid = serializers.SerializerMethodField()
    client_name = serializers.CharField(source="client.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "client", "client_name", "created_by", "service", "amount_due",
            "discount_percent", "real_amount_due", "amount_paid", "remaining_amount",
            "is_fully_paid", "next_due_date", "created_at", "receipts","contract_url"
        ]
        read_only_fields = [
            "id", "client_name", "created_by", "real_amount_due", "amount_paid",
            "remaining_amount", "is_fully_paid", "created_at", "receipts","contract_url"
        ]

    def get_is_fully_paid(self, obj):
        return obj.is_fully_paid

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
