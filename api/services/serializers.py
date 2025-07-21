from rest_framework import serializers
from api.services.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "code", "label", "price"]
        read_only_fields = ["id"]

    def validate_code(self, value):
        """
        Code forcé en MAJUSCULES, espaces remplacés par _
        """
        return value.strip().upper().replace(" ", "_")

    def validate_label(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le libellé du service est trop court.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix doit être positif ou nul.")
        return value

    def create(self, validated_data):
        # Pour garantir même hors formulaire que le code est normalisé
        validated_data["code"] = validated_data["code"].strip().upper().replace(" ", "_")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "code" in validated_data:
            validated_data["code"] = validated_data["code"].strip().upper().replace(" ", "_")
        return super().update(instance, validated_data)