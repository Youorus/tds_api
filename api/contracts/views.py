from django.utils.text import slugify
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.contracts.models import Contract

from api.contracts.permissions import IsContractEditor
from api.contracts.serializer import ContractSerializer
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage, MinioContractStorage
from api.utils.email.leads import send_contract_email_to_lead


class ContractViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        """
        Applique un remboursement partiel ou total sur un contrat.
        Body attendu: { "refund_amount": number, "refund_note": string? }
        Règles:
        - refund_amount > 0
        - refund_amount cumulée <= amount_paid (total perçu)
        """
        contract = self.get_object()
        raw_amount = request.data.get("refund_amount")
        refund_note = request.data.get("refund_note")  # optionnel si tu as ce champ côté modèle/serializer

        from decimal import Decimal, InvalidOperation
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, TypeError):
            return Response({"detail": "Montant invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"detail": "Le montant doit être supérieur à 0."}, status=status.HTTP_400_BAD_REQUEST)

        # Montants déjà payés et déjà remboursés
        already_paid = contract.amount_paid  # propriété safe même sans reçus
        already_refunded = contract.refund_amount or Decimal("0.00")
        max_refundable = (Decimal(already_paid) - already_refunded)

        if amount > max_refundable:
            return Response({
                "detail": f"Le montant dépasse le maximum remboursable ({max_refundable} €)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Appliquer le remboursement (on cumule)
        contract.refund_amount = (already_refunded + amount)
        contract.is_refunded = bool(contract.refund_amount and contract.refund_amount > 0)

        # Si tu gères une note de remboursement côté modèle/serializer, on peut la patcher via serializer
        partial_data = {"refund_amount": str(contract.refund_amount), "is_refunded": contract.is_refunded}
        if refund_note is not None:
            partial_data["refund_note"] = refund_note

        serializer = self.get_serializer(contract, data=partial_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)
    """
    ViewSet principal pour la gestion CRUD des contrats,
    avec endpoints pour uploads PDF, receipts et filtrage par client.
    """
    queryset = Contract.objects.select_related("client", "created_by").prefetch_related("receipts")
    serializer_class = ContractSerializer
    permission_classes = [IsContractEditor]

    def perform_create(self, serializer):
        # Affiche les données POST reçues pour debug
        print("POST data:", self.request.data)
        contract = serializer.save(created_by=self.request.user)
        contract.generate_pdf()  # Génère le PDF APRÈS création

    @action(detail=True, methods=["get"], url_path="receipts")
    def receipts(self, request, pk=None):
        contract = self.get_object()
        receipts = contract.receipts.all()
        serializer = PaymentReceiptSerializer(receipts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="client/(?P<client_id>[^/.]+)")
    def list_by_client(self, request, client_id=None):
        contracts = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(contracts, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Gère la mise à jour partielle du contrat, upload PDF signé,
        et modification du statut "signé".
        """
        instance = self.get_object()
        signed_contract = request.FILES.get("signed_contract")
        is_signed = request.data.get("is_signed", None)
        updated_fields = []

        if signed_contract:
            # 1. Supprimer l'ancien PDF du storage
            if instance.contract_url:
                try:
                    storage = MinioContractStorage()
                    bucket_name = storage.bucket_name
                    path = instance.contract_url.split(f"/{bucket_name}/")[-1]
                    storage.delete(path)
                except Exception as e:
                    print(f"Erreur suppression ancien contrat MinIO : {e}")

            # 2. Sauvegarder le nouveau PDF signé
            storage = MinioContractStorage()
            client = instance.client
            lead = client.lead
            client_id = client.id
            client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client_id}")
            date_str = instance.created_at.strftime("%Y%m%d")
            filename = f"{client_slug}/contrat_{instance.id}_{date_str}.pdf"
            saved_path = storage.save(filename, signed_contract)
            url = storage.url(saved_path)
            instance.contract_url = url
            updated_fields.append("contract_url")

        # 3. MAJ du champ signé
        if is_signed is not None:
            instance.is_signed = str(is_signed).lower() in ["true", "1"]
            updated_fields.append("is_signed")

        # 4. MAJ des autres champs via serializer
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 5. Sauvegarde champs modifiés
        if updated_fields:
            instance.save(update_fields=updated_fields)

        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime un contrat, son PDF et tous ses reçus (et fichiers associés).
        """
        instance = self.get_object()

        # 1. Suppression des reçus liés (PDF storage + DB)
        from api.payments.models import PaymentReceipt  # Adapter si besoin
        receipts = instance.receipts.all()
        for receipt in receipts:
            if receipt.receipt_url:
                try:
                    storage = MinioReceiptStorage()
                    bucket_name = storage.bucket_name
                    path = receipt.receipt_url.split(f"/{bucket_name}/")[-1]
                    storage.delete(path)
                except Exception as e:
                    print(f"Erreur suppression du PDF reçu MinIO : {e}")

        # 2. Suppression du PDF contrat
        if instance.contract_url:
            try:
                storage = MinioContractStorage()
                bucket_name = storage.bucket_name
                path = instance.contract_url.split(f"/{bucket_name}/")[-1]
                storage.delete(path)
            except Exception as e:
                print(f"Erreur suppression du PDF contrat MinIO : {e}")

        # 3. Supprime l’instance (et reçus via FK CASCADE)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="send-email")
    def send_email(self, request, pk=None):
        """
        Envoie le contrat PDF au client concerné par e-mail.
        """
        contract = self.get_object()
        try:
            send_contract_email_to_lead(contract)
        except Exception as e:
            # Logge ou renvoie le détail si besoin
            return Response({"detail": f"Erreur lors de l'envoi de l'email : {e}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Contrat envoyé au client par email."}, status=status.HTTP_200_OK)