from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from api.models import Payment, PaymentReceipt
from api.serializers.payment_serializers import PaymentSerializer, PaymentReceiptSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour la gestion des plans de paiement.
    Inclut une action personnalisée 'pay' pour enregistrer un versement.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.select_related("client", "created_by").prefetch_related("receipts")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="client/(?P<client_id>[^/.]+)")
    def list_by_client(self, request, client_id=None):
        payments = Payment.objects.filter(client_id=client_id).prefetch_related("receipts")
        if not payments.exists():
            raise NotFound("Aucun plan de paiement trouvé pour ce client.")
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        plan = self.get_object()
        data = request.data

        try:
            amount = Decimal(data.get("amount", "0.00"))
            mode = data["mode"]
            next_due_date = data.get("next_due_date")
        except (KeyError, ValueError):
            return Response({"error": "Données invalides."}, status=400)

        if amount <= 0:
            return Response({"error": "Le montant doit être supérieur à zéro."}, status=400)

        total_after = (amount + plan.amount_paid).quantize(Decimal("0.01"))
        if total_after < plan.real_amount_due and not next_due_date:
            return Response({"error": "La prochaine date de paiement est requise."}, status=400)

        try:
            receipt = plan.pay(
                amount=amount,
                mode=mode,
                user=request.user,
                next_due_date=next_due_date,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response(PaymentReceiptSerializer(receipt).data, status=201)