from rest_framework import serializers

from api.statut_dossier.models import StatutDossier


class StatutDossierSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour StatutDossier.
    """
    class Meta:
        model = StatutDossier
        fields = ["id", "code", "label", "color"]