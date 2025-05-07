# api/serializers/user_avatar_serializer.py

from rest_framework import serializers
from api.models import User

class UserAvatarSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'avatar_url']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 'avatar_url']

    def get_avatar_url(self, obj):
        """
        Retourne l'URL complète de l'avatar si disponible.
        """
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None