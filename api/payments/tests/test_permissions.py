import pytest
from rest_framework.test import APIRequestFactory
from api.payments.permissions import IsPaymentEditor
from api.users.models import UserRoles

@pytest.mark.parametrize("role,method,expected", [
    (UserRoles.ADMIN, "POST", True),
    (UserRoles.JURISTE, "POST", True),
    (UserRoles.CONSEILLER, "POST", False),
    (UserRoles.ACCUEIL, "POST", False),
    (UserRoles.ADMIN, "GET", True),
    (UserRoles.CONSEILLER, "GET", True),
])
def test_is_payment_editor_permission(role, method, expected, user_factory):
    user = user_factory(role=role)
    factory = APIRequestFactory()
    request = factory.generic(method, "/receipts/")
    request.user = user

    perm = IsPaymentEditor()
    has_perm = perm.has_permission(request, None)
    assert has_perm is expected