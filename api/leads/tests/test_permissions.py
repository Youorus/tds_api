# leads/tests/test_permissions.py

from api.leads.permissions import IsLeadEditor, IsConseillerOrAdmin
from api.models import User

def get_request_with_role(role):
    class DummyUser:
        is_authenticated = True
        def __init__(self, role): self.role = role
    class DummyRequest:
        user = DummyUser(role)
    return DummyRequest()

def test_is_lead_editor_grants_for_internal_roles():
    """
    Vérifie que tous les rôles internes ont la permission d'éditer un lead.
    """
    for role in ("ADMIN", "ACCUEIL", "JURISTE", "CONSEILLER", "COMPTABILITE"):
        req = get_request_with_role(role)
        perm = IsLeadEditor()
        assert perm.has_permission(req, None)

def test_is_conseiller_or_admin_only():
    """
    Vérifie que seuls les conseillers ou admin peuvent s’assigner un lead.
    """
    assert IsConseillerOrAdmin().has_permission(get_request_with_role("CONSEILLER"), None)
    assert IsConseillerOrAdmin().has_permission(get_request_with_role("ADMIN"), None)
    assert not IsConseillerOrAdmin().has_permission(get_request_with_role("ACCUEIL"), None)