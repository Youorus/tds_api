from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.models import Client


class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Client avec informations utilisateur étendues.

    Champs :
        id: Identifiant client (lecture seule)
        user: Compte utilisateur associé (requis)
        phone: Numéro de téléphone du client (optionnel)
        address: Adresse physique du client (optionnelle)
    """

    phone = serializers.CharField(
        required=False,
        allow_null=True,
        error_messages={
            'invalid': _('Format de numéro de téléphone invalide.')
        }
    )

    class Meta:
        model = Client
        fields = ['id', 'user', 'phone', 'address']
        extra_kwargs = {
            'user': {
                'error_messages': {
                    'does_not_exist': _('Cet utilisateur n\'existe pas.')
                }
            },
            'address': {
                'error_messages': {
                    'blank': _('L\'adresse ne peut pas être vide.')
                }
            }
        }

    def validate_phone(self, value):
        """Valide que le numéro de téléphone ne contient que des chiffres."""
        if value and not value.isdigit():
            raise serializers.ValidationError(
                _("Le numéro de téléphone ne doit contenir que des chiffres.")
            )
        return value