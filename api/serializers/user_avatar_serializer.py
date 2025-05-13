# api/serializers/user_avatar_serializer.py

from rest_framework import serializers
from api.models import User

class UserAvatarSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 'avatar']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar)
            return obj.avatar
        return None