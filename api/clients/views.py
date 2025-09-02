from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.clients.models import Client
from api.clients.permissions import IsClientCreateOpen
from api.clients.serializers import ClientSerializer
from api.contracts.models import Contract
from api.documents.models import Document
from api.leads.models import Lead
from api.payments.models import PaymentReceipt
from api.utils.email.clients.tasks import send_client_account_created_task


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion CRUD des clients.

    - POST /api/clients/ : Création publique (pas d'authentification requise)
    - GET/PUT/PATCH/DELETE : Authentification requise
    """

    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsClientCreateOpen]

    def perform_create(self, serializer):
        """
        Crée un client en le liant éventuellement à un lead existant (via ?id=).
        Vérifie qu’aucun client ou formulaire n’est déjà associé au lead.
        """
        lead_id = self.request.query_params.get("id")
        if not lead_id:
            return serializer.save()

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError({"lead": "Lead introuvable avec cet ID."})

        if hasattr(lead, "form_data") or Client.objects.filter(lead=lead).exists():
            raise ValidationError(
                {"lead": "Un formulaire a déjà été enregistré pour ce lead."}
            )

        client = serializer.save(lead=lead)
        send_client_account_created_task.delay(
            client.id
        )  # ✅ Envoi de l’e-mail RGPD via tâche asynchrone

    def create(self, request, *args, **kwargs):
        """
        Surcharge de la méthode de création pour gérer la liaison avec un lead via `?id=`.
        Valide les données, lie au lead si présent, et déclenche une notification email RGPD.
        """
        lead_id = request.query_params.get("id")
        if lead_id:
            serializer = self.get_serializer(
                data=request.data, context={"skip_type_demande_validation": True}
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)

        return super().create(request, *args, **kwargs)

    from django.db import transaction

    @action(detail=True, methods=["delete"], url_path="cascade-delete")
    @transaction.atomic
    def cascade_delete(self, request, pk=None):
        """
        Supprime un client à partir de l'ID du lead, ainsi que tous les éléments liés :
        - documents du client
        - contrats et reçus de paiement
        - lead lui-même
        - client
        """
        try:
            # ⚠️ On part du lead, puis on récupère le client associé
            lead = Lead.objects.get(pk=pk)
            client = Client.objects.get(lead=lead)

            # Supprimer les documents liés au client
            Document.objects.filter(client=client).delete()

            # Supprimer les reçus liés aux contrats
            contracts = Contract.objects.filter(client=client)
            for contract in contracts:
                PaymentReceipt.objects.filter(contract=contract).delete()

            # Supprimer les contrats
            contracts.delete()

            # Supprimer le lead
            lead.delete()

            # Supprimer le client
            client.delete()

            return Response(
                {
                    "detail": "Client, lead, contrats et documents supprimés avec succès."
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        except Lead.DoesNotExist:
            return Response(
                {"detail": "Lead introuvable."}, status=status.HTTP_404_NOT_FOUND
            )
        except Client.DoesNotExist:
            return Response(
                {"detail": "Client associé au lead introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
