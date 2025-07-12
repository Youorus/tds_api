import pytest
from rest_framework.test import APIRequestFactory
from api.payments.permissions import IsPaymentEditor
from api.users.models import User, UserRoles

@pytest.mark.django_db
class TestIsPaymentEditor:
    def test_permission_for_safe_methods(self):
        user = User.objects.create_user(
            email="test@ex.com", first_name="Test", last_name="User", password="pwd", role=UserRoles.CONSEILLER
        )
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user
        perm = IsPaymentEditor()
        assert perm.has_permission(request, None)

    def test_permission_for_editor_roles(self):
        user = User.objects.create_user(
            email="admin@ex.com", first_name="Admin", last_name="User", password="pwd", role=UserRoles.ADMIN
        )
        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user
        perm = IsPaymentEditor()
        assert perm.has_permission(request, None)

    def test_permission_forbidden_for_non_editor(self):
        # Suppose un utilisateur sans rôle autorisé
        user = User.objects.create_user(
            email="basic@ex.com", first_name="Basic", last_name="User", password="pwd", role="BASIC"
        )
        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user
        perm = IsPaymentEditor()
        assert not perm.has_permission(request, None)