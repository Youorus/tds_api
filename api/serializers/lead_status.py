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

    def validate(self, attrs):
        status = attrs.get("status")
        lead = self.instance  # lead existant qu'on modifie

        if status in [LeadStatus.RDV_PLANIFIER, LeadStatus.RDV_CONFIRME] and not lead.appointment_date:
            raise serializers.ValidationError({
                "status": f"Impossible de passer au statut '{status}' sans rendez-vous planifié."
            })

        return attrs