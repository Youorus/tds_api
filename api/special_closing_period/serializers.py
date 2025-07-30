# serializers/special_closing_period.py

from rest_framework import serializers
from .models import SpecialClosingPeriod

class SpecialClosingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialClosingPeriod
        fields = ["id", "label", "start_date", "end_date"]

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError("La date de fin doit être postérieure ou égale à la date de début.")
        return attrs