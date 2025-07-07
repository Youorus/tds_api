import pytest
from rest_framework.test import APIRequestFactory
from api.contracts.permissions import IsContractEditor
from api.users.roles import UserRoles

@pytest.mark.parametrize("role,method,expected", [
    (UserRoles.ADMIN, "POST", True),
    (UserRoles.JURISTE, "PUT", True),
    (UserRoles.CONSEILLER, "POST", False),
    (UserRoles.ACCUEIL, "POST", False),
    (UserRoles.ADMIN, "GET", True),
    (UserRoles.CONSEILLER, "GET", True),
])
def test_contract_editor_permission(role, method, expected, django_user_model):
    if role is None:
        pytest.skip("Role non défini dans UserRoles")
    user = django_user_model.objects.create_user(email=f"{role}@x.fr", password="pw", role=role)
    factory = APIRequestFactory()
    request = factory.generic(method, "/contracts/")
    request.user = user

    perm = IsContractEditor()
    has_perm = perm.has_permission(request, None)
    assert has_perm is expected