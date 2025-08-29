from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
import logging

from api.leads.models import Lead
from api.payments.models import PaymentReceipt
from api.payments.permissions import IsPaymentEditor
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage
from api.utils.email.recus.tasks import send_receipts_email_task

logger = logging.getLogger(__name__)


class PaymentReceiptViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour gérer les reçus de paiement (PaymentReceipt).
    """
    queryset = PaymentReceipt.objects.select_related("client", "contract", "created_by")
    serializer_class = PaymentReceiptSerializer
    permission_classes = [IsPaymentEditor]

    def perform_create(self, serializer):
        """
        Sauvegarde le reçu avec l'utilisateur connecté, puis génère son PDF.
        """
        receipt = serializer.save(created_by=self.request.user)
        receipt.generate_pdf()

    def create(self, request, *args, **kwargs):
        """
        Empêche la création si le montant est ≤ 0.
        """
        data = request.data.copy()
        try:
            amount = Decimal(data.get("amount", "0"))
        except Exception:
            return Response({"error": "Montant invalide."}, status=400)

        if amount <= 0:
            return Response({"error": "Le montant doit être supérieur à zéro."}, status=400)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime aussi le PDF dans MinIO si présent.
        """
        instance = self.get_object()
        if instance.receipt_url:
            try:
                storage = MinioReceiptStorage()
                bucket_name = storage.bucket_name
                path = instance.receipt_url.split(f"/{bucket_name}/")[-1]
                storage.delete(path)
            except Exception as e:
                logger.warning(f"Erreur suppression du reçu PDF MinIO : {e}")
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="send-email")
    def send_receipts_email(self, request):
        """
        Envoie un ou plusieurs reçus PDF par email au lead concerné.

        Expects: {
            "lead_id": int,
            "receipt_ids": [int, ...]
        }
        """
        lead_id = request.data.get("lead_id")
        receipt_ids = request.data.get("receipt_ids", [])

        if not lead_id or not receipt_ids:
            return Response(
                {"detail": "lead_id et receipt_ids sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sécurité : conversion explicite en entiers
        try:
            receipt_ids = [int(rid) for rid in receipt_ids]
        except (ValueError, TypeError):
            return Response({"detail": "receipt_ids doit contenir des entiers."}, status=400)

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=404)

        if not lead.email:
            return Response({"detail": "Ce lead ne possède pas d’adresse email."}, status=400)

        receipts = PaymentReceipt.objects.filter(id__in=receipt_ids, client__lead=lead)
        if not receipts.exists():
            return Response({"detail": "Aucun reçu trouvé pour ce lead."}, status=404)

        try:
            send_receipts_email_task.delay(lead.id)
        except Exception as e:
            logger.exception("Erreur lors du déclenchement de la task d’envoi des reçus.")
            return Response({"detail": f"Erreur technique : {str(e)}"}, status=500)

        return Response({"detail": "Envoi des reçus programmé avec succès."}, status=200)