from rest_framework import serializers

from api.lead_status.models import LeadStatus


class LeadStatusSerializer(serializers.ModelSerializer):
    """
    Serializer pour exposer les informations publiques d’un statut de lead.
    Utilisé dans les listes déroulantes, le filtrage ou l’affichage détaillé.
    """
    class Meta:
        model = LeadStatus
        fields = ["id", "label", "color", "code"]