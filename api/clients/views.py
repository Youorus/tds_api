from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.clients.models import Client
from api.leads.models import Lead
from api.clients.serializers import ClientSerializer
from api.clients.permissions import IsClientCreateOpen

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
        lead_id = self.request.query_params.get("id")
        if not lead_id:
            return serializer.save()

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError({"lead": "Lead introuvable avec cet ID."})

        if hasattr(lead, "form_data") or Client.objects.filter(lead=lead).exists():
            raise ValidationError({"lead": "Un formulaire a déjà été enregistré pour ce lead."})

        serializer.save(lead=lead)

    def create(self, request, *args, **kwargs):
        lead_id = request.query_params.get("id")
        if lead_id:
            serializer = self.get_serializer(
                data=request.data,
                context={"skip_type_demande_validation": True}
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        return super().create(request, *args, **kwargs)