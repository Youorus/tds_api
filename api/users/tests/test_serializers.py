import pytest

from api.users.roles import UserRoles
from api.users.serializers import UserSerializer


@pytest.mark.django_db
class TestUserSerializer:
    """
    Tests unitaires du serializer UserSerializer.
    Vérifie la validation, la création et les cas d’erreurs.
    """

    def test_valid_serializer(self):
        """
        Vérifie que le serializer accepte des données valides.
        """
        data = {
            "email": "valid@test.com",
            "first_name": "Valid",
            "last_name": "Test",
            "password": "Valid@1234",
            "role": UserRoles.ACCUEIL,
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_email(self):
        """
        Vérifie que le serializer rejette une adresse email invalide.
        """
        data = {
            "email": "invalid",
            "first_name": "Bad",
            "last_name": "Email",
            "password": "Password@123",
            "role": UserRoles.JURISTE,
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_short_password(self):
        """
        Vérifie que le serializer rejette un mot de passe trop court.
        """
        data = {
            "email": "short@test.com",
            "first_name": "Short",
            "last_name": "Pwd",
            "password": "123",
            "role": UserRoles.CONSEILLER,
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_create_user(self):
        """
        Vérifie la création réelle d’un utilisateur via le serializer.
        """
        data = {
            "email": "serializer@test.com",
            "first_name": "Seri",
            "last_name": "Alizer",
            "password": "Strong@Pass123",
            "role": UserRoles.COMPTABILITE,
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.email == "serializer@test.com"
        assert user.check_password("Strong@Pass123")