# api/serializers/lead_status.py

from rest_framework import serializers
from api.models import Lead, LeadStatus

class LeadStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["status"]

    def validate_status(self, value):
        if value not in LeadStatus.values:
            raise serializers.ValidationError("Statut invalide.")
        return value