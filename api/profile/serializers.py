from rest_framework import serializers

from api.users.models import User


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Serializer pour l’upload, la modification et l’affichage de l’avatar utilisateur.
    Tous les champs sauf avatar sont read-only pour l’intégrité.
    """

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']

    def get_avatar_url(self, obj):
        """
        Retourne l’URL absolue de l’avatar si disponible.
        """
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar)
            return obj.avatar
        return None