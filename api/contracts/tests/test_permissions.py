import pytest
from rest_framework.test import APIRequestFactory
from api.contracts.permissions import IsContractEditor
from api.users.models import User, UserRoles

@pytest.mark.django_db
class TestIsContractEditor:
    def test_admin_has_permission(self):
        user = User.objects.create_user(email="admin@ex.com", first_name="Admin", last_name="User", password="pwd", role=UserRoles.ADMIN)
        request = APIRequestFactory().get("/")
        request.user = user
        perm = IsContractEditor()
        assert perm.has_permission(request, None)

    def test_juriste_has_permission(self):
        user = User.objects.create_user(email="juriste@ex.com", first_name="Juriste", last_name="User", password="pwd", role=UserRoles.JURISTE)
        request = APIRequestFactory().post("/")
        request.user = user
        perm = IsContractEditor()
        assert perm.has_permission(request, None)

    def test_random_user_no_permission(self):
        user = User.objects.create_user(email="foo@ex.com", first_name="Foo", last_name="Bar", password="pwd", role="CLIENT")
        request = APIRequestFactory().delete("/")
        request.user = user
        perm = IsContractEditor()
        assert not perm.has_permission(request, None)