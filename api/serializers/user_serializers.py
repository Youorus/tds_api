import re
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle User avec validation complète et exigences de sécurité.
    Gère la création d'utilisateurs avec une politique de mot de passe stricte et validation d'email.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': _('Le mot de passe doit contenir au moins 8 caractères.'),
            'blank': _('Le mot de passe ne peut pas être vide.')
        }
    )

    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': _('L\'email est requis.'),
            'invalid': _('Veuillez entrer une adresse email valide.')
        }
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'first_name': {
                'error_messages': {
                    'blank': _('Le prénom est requis.')
                }
            },
            'last_name': {
                'error_messages': {
                    'blank': _('Le nom de famille est requis.')
                }
            }
        }

    def validate_email(self, value):
        """Valide le format de l'email et son unicité."""
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError(_("Format d'email invalide."))

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Cet email est déjà utilisé."))
        return value

    def validate_password(self, value):
        """
        Applique une politique de mot de passe fort :
        - Minimum 8 caractères
        - Au moins une lettre majuscule
        - Au moins un chiffre
        - Au moins un caractère spécial
        """
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("Le mot de passe doit contenir au moins une lettre majuscule."))

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("Le mot de passe doit contenir au moins un chiffre."))

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise serializers.ValidationError(_("Le mot de passe doit contenir au moins un caractère spécial."))

        return value

    def create(self, validated_data):
        """Hache le mot de passe avant de créer l'utilisateur"""
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)



