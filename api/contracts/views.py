from django.utils.text import slugify
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.contracts.models import Contract

from api.contracts.permissions import IsContractEditor
from api.contracts.serializer import ContractSerializer
from api.payments.serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage, MinioContractStorage

class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion CRUD des contrats,
    avec endpoints pour uploads PDF, receipts et filtrage par client.
    """
    queryset = Contract.objects.select_related("client", "created_by").prefetch_related("receipts")
    serializer_class = ContractSerializer
    permission_classes = [IsContractEditor]

    def perform_create(self, serializer):
        contract = serializer.save(created_by=self.request.user)
        contract.generate_pdf()   # Génère le PDF APRES création

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