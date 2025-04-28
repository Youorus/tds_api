from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.models import Lead
from api.services.email_service import EmailService

class SendFormulaireEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lead_id = request.data.get("lead_id")
        if not lead_id:
            return Response({"error": "lead_id manquant"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response({"error": "Lead introuvable"}, status=status.HTTP_404_NOT_FOUND)

        success = EmailService().send_formulaire_email(lead)

        if success:
            return Response({"message": "Email envoyé avec succès"})
        else:
            return Response({"error": "Erreur lors de l'envoi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)