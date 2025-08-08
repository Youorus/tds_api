# users/serializers.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from api.users.models import User
from api.users.roles import UserRoles


class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur principal pour les utilisateurs.
    Gère la création, la mise à jour, et expose toujours l’avatar en URL absolue.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        allow_blank=True,
        help_text=_("Mot de passe (requis uniquement à la création)")
    )
    role = serializers.ChoiceField(
        choices=UserRoles.choices,
        required=True,
        help_text=_("Rôle de l'utilisateur")
    )
    # Ajout PRO : toujours renvoyer une URL complète (http…) pour l’avatar
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "is_staff", "is_superuser", "is_active",
            "date_joined", "avatar",   # Ajoute "avatar" ici
            "password"
        ]
        read_only_fields = ("is_staff", "is_superuser", "date_joined", "id")

    def get_avatar(self, obj):
        """
        Retourne toujours une URL absolue pour l’avatar,
        que ce soit stocké comme URL ou chemin relatif.
        """
        if not obj.avatar:
            return None
        request = self.context.get("request")
        # Si l'avatar n'est pas déjà une URL, on la construit
        if request and not obj.avatar.startswith("http"):
            return request.build_absolute_uri(obj.avatar)
        return obj.avatar

    def create(self, validated_data):
        """
        Création sécurisée d'un utilisateur.
        Applique les permissions selon le rôle.
        """
        password = validated_data.pop("password", None)
        role = validated_data.get("role")

        # Vérifie que le mot de passe est fourni
        if not password:
            raise serializers.ValidationError({
                "password": _("Le mot de passe est requis lors de la création.")
            })

        # Normalise le rôle (str) si besoin
        if isinstance(role, UserRoles):
            validated_data["role"] = role.value

        user = User(**validated_data)
        user.set_password(password)
        user.set_role_permissions()
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Mise à jour partielle d’un utilisateur.
        Ne traite pas le mot de passe ici.
        """
        validated_data.pop("password", None)

        role = validated_data.get("role")
        if role:
            if isinstance(role, UserRoles):
                validated_data["role"] = role.value
            instance.role = validated_data["role"]
            instance.set_role_permissions()

        return super().update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Sérialiseur pour le changement de mot de passe.
    Nécessite l’ancien mot de passe et le nouveau.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context.get("user")
        if not user or not user.check_password(value):
            raise serializers.ValidationError(_("Ancien mot de passe incorrect."))
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(_("Le mot de passe doit faire au moins 8 caractères."))
        return value