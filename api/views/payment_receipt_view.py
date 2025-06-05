from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from api.models import PaymentReceipt
from api.serializers.payment_serializers import PaymentReceiptSerializer


class PaymentReceiptViewSet(viewsets.ModelViewSet):
    """
    Vue de gestion des reçus de paiement.
    - Création directe interdite (passer par Payment.pay()).
    - Mise à jour interdite (pas de modification d’un reçu existant).
    - Le PDF est généré automatiquement à la création via Payment.pay().
    """
    queryset = PaymentReceipt.objects.select_related("client", "plan", "created_by")
    serializer_class = PaymentReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        raise NotImplementedError("Utilisez le endpoint /payments/{id}/pay/ pour créer un reçu.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="La modification d’un reçu est interdite.")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH", detail="La modification d’un reçu est interdite.")