from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()


class LoginSerializer(serializers.Serializer):
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
        email = attrs.get('email').lower()  # Normalisation de l'email
        password = attrs.get('password')
        request = self.context.get('request')
        errors = {}

        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            errors['email'] = _("Aucun utilisateur trouvé avec cet email.")
            raise serializers.ValidationError(errors)

        user = authenticate(request=request, email=email, password=password)

        if not user:
            errors['password'] = _("Mot de passe incorrect.")
            raise serializers.ValidationError(errors)

        if not user.is_active:
            errors['non_field_errors'] = _("Votre compte est désactivé. Veuillez contacter l'administrateur.")
            raise serializers.ValidationError(errors)

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }