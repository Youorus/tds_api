from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from api.models import Role, Client
from api.serializers.login_serializer import LoginSerializer

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = serializer.validated_data['tokens']

        # Récupération des données utilisateur
        role = self._get_user_role(user)
        client_data = self._get_client_data(user)

        # Construction de la réponse
        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": role,
                **client_data
            },
            "tokens": tokens  # Inclure directement les tokens dans la réponse JSON
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _get_user_role(self, user):
        """Détermine le rôle de l'utilisateur"""
        if hasattr(user, 'role') and user.role:
            return user.role.role_type
        elif user.is_superuser:
            return Role.RoleType.ADMIN.value
        elif user.is_staff:
            return Role.RoleType.CONSEILLER.value
        return Role.RoleType.CLIENT.value

    def _get_client_data(self, user):
        """Récupère les données supplémentaires du client"""
        try:
            client_profile = user.client_profile
            return {
                'phone': client_profile.phone,
                'address': client_profile.address
            }
        except Client.DoesNotExist:
            return {}