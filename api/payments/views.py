from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal

from api.leads.models import Lead
from api.payments.models import PaymentReceipt
from api.payments.permissions import IsPaymentEditor
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage
from api.utils.email.notif import send_receipts_email_to_lead


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

    @action(detail=False, methods=["post"], url_path="send-email")
    def send_receipts_email(self, request):
        """
        Envoie un ou plusieurs reçus sélectionnés par email au client.
        Expects: { lead_id, receipt_ids: [id1, id2, ...] }
        """
        lead_id = request.data.get("lead_id")
        receipt_ids = request.data.get("receipt_ids", [])
        if not lead_id or not receipt_ids:
            return Response({"detail": "lead_id et receipt_ids requis"}, status=400)

        # On force receipt_ids en int (important si appel JS/TS)
        try:
            receipt_ids = [int(rid) for rid in receipt_ids]
        except Exception:
            return Response({"detail": "receipt_ids doit contenir des entiers."}, status=400)

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=404)

        receipts = PaymentReceipt.objects.filter(id__in=receipt_ids)
        receipts_list = list(receipts)
        if not receipts_list:
            return Response({"detail": "Aucun reçu trouvé."}, status=404)

        try:
            send_receipts_email_to_lead(lead, receipts_list)
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Log plus complet pour debug
            return Response({"detail": f"Erreur lors de l'envoi de l'email : {e}"}, status=400)
        return Response({"detail": "Reçus envoyés au client par email."})