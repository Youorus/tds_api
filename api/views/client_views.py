from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from api.models import Client, Lead
from api.serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_create(self, serializer):
        lead_id = self.request.query_params.get("id")
        if not lead_id:
            raise ValidationError({"lead": "L'identifiant du lead est requis dans l'URL (?id=...)."})

        try:
            lead = Lead.objects.get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError({"lead": "Lead introuvable avec cet ID."})

        if hasattr(lead, "form_data"):
            raise ValidationError({"lead": "Un formulaire a déjà été enregistré pour ce lead."})

        serializer.save(lead=lead)