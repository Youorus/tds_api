# serializers/opening_hours.py

from rest_framework import serializers
from .models import OpeningHours

class OpeningHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)
    is_closed = serializers.BooleanField(read_only=True)

    class Meta:
        model = OpeningHours
        fields = ["id", "day_of_week", "day_name", "open_time", "close_time", "is_closed"]