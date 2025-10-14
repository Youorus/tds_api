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
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsClientCreateOpen]

    def perform_create(self, serializer):
        """
        Crée ou met à jour un client lié à un lead.
        - Si le lead n’a pas encore de client → création
        - Si un client existe déjà pour ce lead → mise à jour (PATCH)
        """
        lead_id = self.request.query_params.get("id")
        if not lead_id:
            return serializer.save()

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError({"lead": "Lead introuvable avec cet ID."})

        # Vérifier si un client existe déjà pour ce lead
        existing_client = Client.objects.filter(lead=lead).first()

        if existing_client:
            # 🔄 Mise à jour du client existant
            serializer.instance = existing_client
            updated_client = serializer.save()
            return updated_client

        # Sinon création
        client = serializer.save(lead=lead)
        send_client_account_created_task.delay(client.id)
        return client

    def create(self, request, *args, **kwargs):
        """
        Surcharge de la création :
        - Si `?id=` fourni → création ou mise à jour liée au lead
        - Sinon, création classique
        """
        lead_id = request.query_params.get("id")
        if lead_id:
            serializer = self.get_serializer(
                data=request.data,
                context={"skip_type_demande_validation": True},
                partial=True,  # ⚡ permet la mise à jour partielle
            )
            serializer.is_valid(raise_exception=True)
            client = self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)
            return Response(
                ClientSerializer(client).data,  # retourne les données à jour
                status=status.HTTP_200_OK,      # ⚡ 200 si update, 201 si new
                headers=headers,
            )

        return super().create(request, *args, **kwargs)
