from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from decimal import Decimal

from api.payments.models import PaymentReceipt
from api.payments.permissions import IsPaymentEditor
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage
# from api.permissions.payment import IsPaymentEditor  # Active si tu veux

class PaymentReceiptViewSet(viewsets.ModelViewSet):
    queryset = PaymentReceipt.objects.select_related("client", "contract", "created_by")
    serializer_class = PaymentReceiptSerializer
    permission_classes = [IsPaymentEditor]

    def perform_create(self, serializer):
        receipt = serializer.save(created_by=self.request.user)
        receipt.generate_pdf()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        amount = Decimal(data.get("amount", "0"))
        if amount <= 0:
            return Response({"error": "Le montant doit être supérieur à zéro."}, status=400)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.receipt_url:
            try:
                storage = MinioReceiptStorage()
                bucket_name = storage.bucket_name
                path = instance.receipt_url.split(f"/{bucket_name}/")[-1]
                storage.delete(path)
            except Exception as e:
                print(f"Erreur suppression du reçu PDF MinIO : {e}")
        return super().destroy(request, *args, **kwargs)