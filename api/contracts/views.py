"""
Vues REST API pour la gestion des contrats dans TDS France.

Cette vue inclut les fonctionnalités suivantes :
- Création et mise à jour des contrats
- Envoi de contrats signés
- Téléchargement et suppression des fichiers PDF
- Remboursement partiel ou total
- Recherche de reçus associés
- Envoi du contrat au client par e-mail via une tâche asynchrone
"""
from decimal import Decimal

from django.utils.text import slugify
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.contracts.models import Contract

from api.contracts.permissions import IsContractEditor
from api.contracts.serializer import ContractSerializer
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage, MinioContractStorage
from api.utils.email.contracts.tasks import send_contract_email_task


class ContractViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        """
        Applique un remboursement partiel ou total sur un contrat existant.

        - Le montant doit être supérieur à 0
        - Le total remboursé ne peut pas dépasser le montant déjà payé

        Attendu dans le corps : {
          "refund_amount": number,
          "refund_note": string (optionnel)
        }
        """
        contract = self.get_object()
        raw_amount = request.data.get("refund_amount")
        refund_note = request.data.get("refund_note")  # optionnel si tu as ce champ côté modèle/serializer

        from decimal import Decimal, InvalidOperation
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, TypeError):
            return Response({"detail": "Montant invalide."}, status=status.HTTP_400_BAD_REQUEST)

        valid, message = self._is_valid_refund_amount(contract, amount)
        if not valid:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        # Appliquer le remboursement (on cumule)
        already_refunded = contract.refund_amount or Decimal("0.00")
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
        """
        Méthode appelée à la création d’un contrat.

        Elle associe le créateur et génère automatiquement le PDF du contrat.
        """
        # Affiche les données POST reçues pour debug
        print("POST data:", self.request.data)
        contract = serializer.save(created_by=self.request.user)
        contract.generate_pdf()  # Génère le PDF APRÈS création

    @action(detail=True, methods=["get"], url_path="receipts")
    def receipts(self, request, pk=None):
        """
        Retourne la liste des reçus de paiement associés au contrat.
        """
        contract = self.get_object()
        receipts = contract.receipts.all()
        serializer = PaymentReceiptSerializer(receipts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="client/(?P<client_id>[^/.]+)")
    def list_by_client(self, request, client_id=None):
        """
        Liste les contrats filtrés par identifiant client.
        """
        contracts = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(contracts, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Met à jour partiellement un contrat.

        - Permet de téléverser un PDF signé
        - Permet de modifier le statut `is_signed`
        """
        instance = self.get_object()
        signed_contract = request.FILES.get("signed_contract")
        is_signed = request.data.get("is_signed", None)
        updated_fields = []

        if signed_contract:
            # 1. Supprimer l'ancien PDF du storage
            if instance.contract_url:
                self._delete_file_from_url(MinioContractStorage(), instance.contract_url)

            # 2. Sauvegarder le nouveau PDF signé
            instance.contract_url = self._save_signed_contract_pdf(instance, signed_contract)
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
        Supprime un contrat ainsi que tous ses reçus et fichiers PDF associés (contrat et reçus).

        Les suppressions sont faites côté MinIO et en base.
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
                    print(f"Erreur suppression du PDF reçu MinIO: {e}")

        # 2. Suppression du PDF contrat
        if instance.contract_url:
            try:
                storage = MinioContractStorage()
                bucket_name = storage.bucket_name
                path = instance.contract_url.split(f"/{bucket_name}/")[-1]
                storage.delete(path)
            except Exception as e:
                print(f"Erreur suppression du PDF contrat MinIO: {e}")

        # 3. Supprime l’instance (et reçus via FK CASCADE)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="send-email")
    def send_email(self, request, pk=None):
        """
        Envoie le contrat par e-mail au client via une tâche Celery.

        Le contrat PDF est envoyé en pièce jointe si disponible.
        """
        contract = self.get_object()
        send_contract_email_task.delay(contract.id)
        return Response({"detail": "📨 L'e-mail de contrat va être envoyé dans quelques instants."}, status=status.HTTP_202_ACCEPTED)

    def _delete_file_from_url(self, storage, file_url: str):
        """
        Supprime un fichier du storage MinIO à partir de son URL.

        - `storage` : instance de stockage MinIO
        - `file_url` : URL complète du fichier à supprimer
        """
        try:
            bucket = storage.bucket_name
            path = file_url.split(f"/{bucket}/")[-1]
            storage.delete(path)
        except Exception as e:
            print(f"Erreur suppression fichier MinIO: {e}")

    def _save_signed_contract_pdf(self, instance, file):
        """
        Sauvegarde un fichier PDF signé dans MinIO et retourne son URL publique.

        Le chemin est construit dynamiquement à partir du nom du client et de la date.
        """
        client = instance.client
        lead = client.lead
        client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client.id}")
        date_str = instance.created_at.strftime("%Y%m%d")
        filename = f"{client_slug}/contrat_{instance.id}_{date_str}.pdf"

        storage = MinioContractStorage()
        saved_path = storage.save(filename, file)
        return storage.url(saved_path)

    def _is_valid_refund_amount(self, contract, amount: Decimal) -> tuple[bool, str]:
        """
        Vérifie si un montant de remboursement est valide par rapport au montant payé.

        Retourne un tuple : (valide: bool, message: str)
        """
        already_paid = contract.amount_paid
        already_refunded = contract.refund_amount or Decimal("0.00")
        max_refundable = already_paid - already_refunded

        if amount <= 0:
            return False, "Le montant doit être supérieur à 0."
        if amount > max_refundable:
            return False, f"Le montant dépasse le maximum remboursable ({max_refundable} €)."
        return True, ""