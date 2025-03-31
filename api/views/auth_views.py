from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Role, Client
from api.serializers import LoginSerializer
from tds import settings


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
        tokens = serializer.validated_data['tokens']  # Récupère les tokens JWT

        # Récupération du rôle de l'utilisateur
        role = None
        try:
            role = user.role.role_type  # Accès via la relation OneToOne
        except Role.DoesNotExist:
            if user.is_superuser:
                role = Role.RoleType.ADMIN.value
            elif user.is_staff:
                role = Role.RoleType.CONSEILLER.value
            else:
                role = Role.RoleType.CLIENT.value

        # Récupération des infos supplémentaires du client (si existant)
        client_data = {}
        try:
            client_profile = user.client_profile
            client_data = {
                'phone': client_profile.phone,
                'address': client_profile.address
            }
        except Client.DoesNotExist:
            pass

        # Réponse JSON SANS les tokens
        response_data = {
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": role,
                **client_data
            }
        }

        # Création de la réponse
        response = Response(response_data, status=status.HTTP_200_OK)

        # Ajout des tokens UNIQUEMENT dans les cookies
        self._set_auth_cookies(response, tokens)

        return response

    def _set_auth_cookies(self, response, tokens):
        """Configure les cookies HTTP Only pour les tokens JWT"""
        cookie_params = {
            'secure': not settings.DEBUG,  # Secure en production seulement
            'httponly': True,  # Empêche l'accès via JavaScript
            'samesite': 'Lax',  # Protection contre les attaques CSRF
            'path': settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            'domain': settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN'),  # Optionnel
        }

        # Cookie pour le token d'accès
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'],
            value=tokens['access'],
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            **cookie_params
        )

        # Cookie pour le token de rafraîchissement
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            value=tokens['refresh'],
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            **cookie_params
        )