from rest_framework import serializers
from api.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8, allow_blank=True)
    role = serializers.ChoiceField(choices=User.Roles.choices, required=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "is_staff", "is_superuser", "is_active",
            "date_joined", "password"
        ]
        read_only_fields = ("is_staff", "is_superuser", "date_joined", "id")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        role = validated_data.get("role", None)

        if isinstance(role, User.Roles):
            role = role.value
            validated_data["role"] = role

        # Affecte les droits selon le rôle
        if role == User.Roles.ADMIN:
            validated_data["is_staff"] = True
            validated_data["is_superuser"] = True
        elif role in [
            User.Roles.ACCUEIL,
            User.Roles.JURISTE,
            User.Roles.CONSEILLER,
            User.Roles.COMPTABILITE
        ]:
            validated_data["is_staff"] = True
            validated_data["is_superuser"] = False
        else:
            validated_data["is_staff"] = False
            validated_data["is_superuser"] = False

        user = User(**validated_data)

        if password:
            user.set_password(password)
        else:
            raise serializers.ValidationError({"password": "Le mot de passe est requis lors de la création."})

        user.save()
        return user

    def update(self, instance, validated_data):
        # Ne jamais modifier le mot de passe ici
        validated_data.pop("password", None)

        role = validated_data.get("role", None)
        if role is not None:
            if role == User.Roles.ADMIN:
                instance.is_staff = True
                instance.is_superuser = True
            elif role in [
                User.Roles.ACCUEIL,
                User.Roles.JURISTE,
                User.Roles.CONSEILLER,
                User.Roles.COMPTABILITE,
            ]:
                instance.is_staff = True
                instance.is_superuser = False
            else:
                instance.is_staff = False
                instance.is_superuser = False

        return super().update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["user"]
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Le mot de passe doit faire au moins 8 caractères.")
        return value