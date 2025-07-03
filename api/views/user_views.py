from django.contrib.auth.password_validation import validate_password
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import User
from api.serializers.user_serializers import UserSerializer


class IsAdminRole(permissions.BasePermission):
    """
    Autorise seulement les utilisateurs avec le rôle ADMIN.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "ADMIN"

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour la gestion CRUD des utilisateurs + changement de mot de passe.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole, IsAuthenticated]
    pagination_class = None

    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email']

    @action(detail=True, methods=["patch"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response({"is_active": "Ce champ est requis."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = bool(is_active)
        user.save()
        return Response({"is_active": user.is_active}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="change-password")
    def change_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"new_password": "Le nouveau mot de passe est requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que ce n'est pas le même que l'actuel
        if user.check_password(new_password):
            return Response({"new_password": "Le nouveau mot de passe doit être différent de l'actuel."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validation de la complexité du mot de passe (via validate_password)
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({"new_password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response( status=status.HTTP_200_OK)