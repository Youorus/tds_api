import pytest
from users.permissions import IsAdminRole
from users.models import User
from rest_framework.test import APIRequestFactory

@pytest.mark.django_db
class TestIsAdminRole:
    """
    Tests unitaires pour la permission IsAdminRole.
    Garantit que seuls les administrateurs ont l'accès.
    """

    def test_permission_granted_for_admin(self):
        """
        Doit autoriser un utilisateur ayant le rôle ADMIN.
        """
        factory = APIRequestFactory()
        user = User.objects.create_superuser("admin@ex.com", "Ad", "Min", "adminpass")
        request = factory.get("/")
        request.user = user
        perm = IsAdminRole()
        assert perm.has_permission(request, None)

    def test_permission_denied_for_non_admin(self):
        """
        Doit refuser l'accès à un utilisateur non-admin.
        """
        factory = APIRequestFactory()
        user = User.objects.create_user("user@ex.com", "Use", "Rr", "userpass")
        request = factory.get("/")
        request.user = user
        perm = IsAdminRole()
        assert not perm.has_permission(request, None)