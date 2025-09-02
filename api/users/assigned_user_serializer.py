# assigned_user_serializer.py
from rest_framework import serializers

from api.users.models import User


class AssignedUserSerializer(serializers.ModelSerializer):
    """
    Serializer indépendant (projection du User pour les usages ‘assigné à’).
    """

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "avatar")
