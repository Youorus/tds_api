import pytest

from api.users.models import User
from api.users.roles import UserRoles


@pytest.mark.django_db
class TestUserModel:
    """
    Tests unitaires du modèle User.
    Garantit la cohérence de la création et des méthodes associées.
    """

    def test_create_user(self):
        """
        Vérifie qu'on peut créer un utilisateur classique avec tous les champs requis.
        """
        user = User.objects.create_user(
            email="user@test.com",
            first_name="Jean",
            last_name="Dupont",
            password="Secret@123",
            role=UserRoles.CONSEILLER,
        )
        assert user.email == "user@test.com"
        assert user.check_password("Secret@123")
        assert user.is_active
        assert user.role == UserRoles.CONSEILLER

    def test_create_superuser(self):
        """
        Vérifie la création correcte d'un super-utilisateur (is_staff et is_superuser).
        """
        user = User.objects.create_superuser(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            password="Admin@123"
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.role == UserRoles.ADMIN

    def test_str_and_full_name(self):
        """
        Vérifie la représentation textuelle et la méthode get_full_name().
        """
        user = User.objects.create_user(
            email="str@test.com",
            first_name="Alice",
            last_name="Wonder",
            password="Wonder@123",
            role=UserRoles.JURISTE,
        )
        assert str(user) == "str@test.com (Alice Wonder)"
        assert user.get_full_name() == "Alice Wonder"
        assert user.get_short_name() == "Alice"