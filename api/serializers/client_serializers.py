from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.models import Client


from rest_framework import serializers

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        exclude = ["id", "lead"]  # ou `fields = "__all__"` si tu veux tout