from rest_framework import serializers
from api.models import StatutDossier

class StatutDossierSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutDossier
        fields = ["id", "code", "label", "color"]