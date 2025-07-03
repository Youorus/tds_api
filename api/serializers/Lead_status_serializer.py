from rest_framework import serializers
from api.models import LeadStatus

class LeadStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadStatus
        fields = ["id", "label", "color", "code"]