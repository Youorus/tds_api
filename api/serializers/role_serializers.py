from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.models import Role


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Role avec validation du type de rôle.
    Garantit que seuls les superutilisateurs peuvent avoir le rôle ADMIN.
    """

    role_type = serializers.ChoiceField(
        choices=Role.RoleType.choices,
        error_messages={
            'invalid_choice': _('Rôle invalide. Choix valides : {choices}.'),
            'required': _('Le rôle est requis.')
        }
    )

    class Meta:
        model = Role
        fields = ['id', 'user', 'role_type', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {
                'error_messages': {
                    'does_not_exist': _('Cet utilisateur n\'existe pas.')
                }
            }
        }

    def validate(self, data):
        """Valide que seuls les superutilisateurs peuvent être ADMIN"""
        if data.get('role_type') == Role.RoleType.ADMIN and not data.get('user').is_superuser:
            raise serializers.ValidationError({
                'role_type': _('Seuls les superutilisateurs peuvent avoir le rôle ADMIN.')
            })
        return data