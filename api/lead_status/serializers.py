from rest_framework import serializers
from api.models import Lead, LeadStatus

class LeadStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour du statut d’un Lead uniquement.
    Valide la cohérence métier (ex : impossible de passer à RDV_PLANIFIE/RDV_CONFIRME sans rendez-vous).
    """
    class Meta:
        model = Lead
        fields = ["status"]

    def validate_status(self, value):
        """
        Vérifie que le statut fourni existe bien parmi les statuts configurés.
        """
        if not LeadStatus.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Statut invalide.")
        return value

    def validate(self, attrs):
        """
        Règle métier : Si on passe à RDV_PLANIFIE/RDV_CONFIRME, il faut obligatoirement un rendez-vous.
        """
        status = attrs.get("status")
        lead = self.instance  # Instance du lead actuel

        # On centralise les codes dynamiques des statuts
        codes_needing_rdv = {"RDV_PLANIFIE", "RDV_CONFIRME"}

        if status and status.code in codes_needing_rdv and not lead.appointment_date:
            raise serializers.ValidationError({
                "status": f"Impossible de passer au statut '{status.label}' sans rendez-vous planifié."
            })

        return attrs