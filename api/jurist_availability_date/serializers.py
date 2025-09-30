# api/serializers/jurist_availability_date.py

from rest_framework import serializers

from api.jurist_availability_date.models import JuristGlobalAvailability


class JuristGlobalAvailabilitySerializer(serializers.ModelSerializer):

    date = serializers.DateField()
    repeat_weekly = serializers.BooleanField()

    class Meta:
        model = JuristGlobalAvailability
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "repeat_weekly",
        ]
