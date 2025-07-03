from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import Client, Lead
from api.serializers.client_serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des clients.
    - POST /api/clients/ : Création publique (pas d'auth requise)
    - GET/PUT/PATCH/DELETE : Authentification requise
    """

    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_permissions(self):
        # Rends la route POST (create) accessible à tous, les autres actions nécessitent l'authentification
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        lead_id = self.request.query_params.get("id")

        # Cas création manuelle (pas de lead lié explicitement)
        if not lead_id:
            return serializer.save()

        # Création à partir d’un lead existant
        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError({"lead": "Lead introuvable avec cet ID."})

        # Vérifie qu'un formulaire n'est pas déjà lié à ce lead
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