import re
from django.contrib.auth import get_user_model, authenticate
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


class LoginSerializer(serializers.Serializer):
    """
    Serializer de connexion pour authentifier un utilisateur avec email et mot de passe.
    Retourne les tokens JWT (access + refresh) si l'authentification est réussie.
    """

    email = serializers.EmailField(
        error_messages={
            'required': _('L\'email est requis.'),
            'invalid': _('Veuillez entrer une adresse email valide.')
        }
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        error_messages={
            'required': _('Le mot de passe est requis.'),
            'blank': _('Le mot de passe ne peut pas être vide.')
        }
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')
        errors = {}

        # Vérifie que l'utilisateur existe
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            errors['email'] = [_("Aucun utilisateur trouvé avec cet email.")]
            raise serializers.ValidationError(errors)

        # Authentifie l'utilisateur
        user = authenticate(request=request, email=email, password=password)

        if not user:
            errors['password'] = [_("Mot de passe incorrect.")]
            raise serializers.ValidationError(errors)

        if not user.is_active:
            errors['non_field_errors'] = [_("Votre compte est désactivé. Veuillez contacter l'administrateur.")]
            raise serializers.ValidationError(errors)

        # Génère les tokens JWT
        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }