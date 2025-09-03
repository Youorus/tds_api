# api/serializers/jurist_availability_date.py

from rest_framework import serializers

from api.jurist_availability_date.models import JuristGlobalAvailability


class JuristGlobalAvailabilitySerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = JuristGlobalAvailability
        fields = [
            "id",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
        ]
