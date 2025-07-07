from rest_framework.permissions import BasePermission

from api.users.roles import UserRoles


class IsLeadEditor(BasePermission):
    """
    Autorise tous les rôles internes à éditer/créer/supprimer un lead,
    sauf pour les actions d’assignation.
    """
    allowed_roles = set(UserRoles.values)  # ('ADMIN', 'ACCUEIL', ...)

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) in self.allowed_roles
        )

class IsConseillerOrAdmin(BasePermission):
    """
    Seuls les conseillers ou admins peuvent s’assigner ou désassigner un lead.
    """
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            getattr(user, "role", None) in (UserRoles.ADMIN, UserRoles.CONSEILLER)
        )