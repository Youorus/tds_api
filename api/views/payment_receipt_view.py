from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from api.models import PaymentReceipt
from decimal import Decimal

from api.serializers.payment_serializers import PaymentReceiptSerializer
from api.storage_backends import MinioReceiptStorage


class PaymentReceiptViewSet(viewsets.ModelViewSet):
    queryset = PaymentReceipt.objects.select_related("client", "contract", "created_by")
    serializer_class = PaymentReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Création classique, receipt généré APRES la sauvegarde
        receipt = serializer.save(created_by=self.request.user)
        # On déclenche la génération du PDF APRES l'enregistrement
        receipt.generate_pdf()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        amount = Decimal(data.get("amount", "0"))
        if amount <= 0:
            return Response({"error": "Le montant doit être supérieur à zéro."}, status=400)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Supprimer le PDF associé du bucket si présent
        if instance.receipt_url:
            try:
                storage = MinioReceiptStorage()
                # Extrait le chemin du fichier à partir de l’URL publique
                # Supposons que l’URL est de la forme http://localhost:9000/recus/slug_id_date.pdf
                # On récupère le chemin après le nom du bucket
                bucket_name = storage.bucket_name
                path = instance.receipt_url.split(f"/{bucket_name}/")[-1]
                storage.delete(path)
            except Exception as e:
                print(f"Erreur suppression du reçu PDF MinIO : {e}")

        # Supprime l’instance en base
        return super().destroy(request, *args, **kwargs)