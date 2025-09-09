import logging
from decimal import Decimal

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date, timedelta
from datetime import datetime

from api.leads.models import Lead
from api.payments.models import PaymentReceipt
from api.payments.permissions import IsPaymentEditor
from api.payments.serializers import PaymentReceiptSerializer
from api.utils.cloud.scw.bucket_utils import delete_object
from api.utils.email.recus.tasks import send_receipts_email_task
from api.utils.email.recus.tasks import send_due_date_updated_email_task
from api.contracts.models import Contract

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
            return Response(
                {"error": "Le montant doit être supérieur à zéro."}, status=400
            )

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime aussi le PDF dans S3 (Scaleway/MinIO) si présent.
        """
        instance = self.get_object()
        if instance.receipt_url:
            try:
                from django.conf import settings

                bucket_name = settings.SCW_BUCKETS["receipts"]
                split_token = f"/{bucket_name}/"
                path = instance.receipt_url.split(split_token, 1)[-1]
                delete_object("receipts", path)
            except Exception as e:
                logger.warning(f"Erreur suppression du reçu PDF S3 : {e}")
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            receipt_ids = [int(rid) for rid in receipt_ids]
        except (ValueError, TypeError):
            return Response(
                {"detail": "receipt_ids doit contenir des entiers."}, status=400
            )

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            return Response({"detail": "Lead introuvable."}, status=404)

        if not lead.email:
            return Response(
                {"detail": "Ce lead ne possède pas d’adresse email."}, status=400
            )

        receipts = PaymentReceipt.objects.filter(id__in=receipt_ids, client__lead=lead)
        if not receipts.exists():
            return Response({"detail": "Aucun reçu trouvé pour ce lead."}, status=404)

        try:
            send_receipts_email_task.delay(lead.id)
        except Exception as e:
            logger.exception(
                "Erreur lors du déclenchement de la task d’envoi des reçus."
            )
            return Response({"detail": f"Erreur technique : {str(e)}"}, status=500)

        return Response(
            {"detail": "Envoi des reçus programmé avec succès."}, status=200
        )

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming_payments(self, request):
        """
        Retourne la liste de tous les paiements à venir (next_due_date ≥ aujourd’hui),
        triés par date croissante, pour les contrats avec un solde dû.
        """
        today = date.today()

        # Étape 1 : requête SQL uniquement sur les champs existants
        receipts = (
            PaymentReceipt.objects
            .filter(
                contract__created_by=request.user,
                next_due_date__gte=today,
            )
            .select_related("contract", "client__lead")
            .order_by("next_due_date")
        )

        # Étape 2 : filtrage Python sur la propriété balance_due
        filtered_receipts = [
            r for r in receipts if r.contract and r.contract.balance_due > 0
        ]

        # Construction de la réponse
        results = []
        for receipt in filtered_receipts:
            results.append({
                "receipt_id": receipt.id,
                "contract_id": receipt.contract.id,
                "client_id": receipt.client.id,
                "first_name": receipt.client.lead.first_name,
                "last_name": receipt.client.lead.last_name,
                "phone": receipt.client.lead.phone,
                "next_due_date": receipt.next_due_date,
                "balance_due": str(receipt.contract.balance_due),
            })

        return Response(results)

    @action(detail=True, methods=["patch"], url_path="update-due-date")
    def update_next_due_date(self, request, pk=None):
        """
        Met à jour la prochaine date d'échéance d’un reçu lié à un contrat.
        """
        try:
            receipt = self.get_object()
        except PaymentReceipt.DoesNotExist:
            return Response({"detail": "Reçu introuvable."}, status=404)

        new_date = request.data.get("next_due_date")
        if not new_date:
            return Response({"next_due_date": "Ce champ est requis."}, status=400)

        try:
            parsed_date = datetime.fromisoformat(new_date).date()
        except ValueError:
            return Response({
                "next_due_date": "Format de date invalide. Utilisez YYYY-MM-DD ou YYYY-MM-DDTHH:MM."
            }, status=400)

        receipt.next_due_date = parsed_date
        receipt.save(update_fields=["next_due_date"])

        try:
            send_due_date_updated_email_task.delay(receipt.id, parsed_date.isoformat())
        except Exception as e:
            logger.exception("Erreur lors de l’envoi de l’email de mise à jour de l’échéance.")

        return Response({
            "receipt_id": receipt.id,
            "contract_id": receipt.contract.id if receipt.contract else None,
            "client": str(receipt.client),
            "new_next_due_date": parsed_date,
        })
