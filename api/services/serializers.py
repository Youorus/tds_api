from rest_framework import serializers
from api.services.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "code", "label", "price"]
        read_only_fields = ["id"]

    def validate_label(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le libellé du service est trop court.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix doit être positif ou nul.")
        return value