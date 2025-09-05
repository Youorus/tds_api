from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from api.custom_auth.serializers import LoginSerializer
from django.conf import settings

User = get_user_model()
IS_HTTPS = not settings.DEBUG  # HTTPS en production

# 🔐 Paramètres communs pour les cookies
COMMON_COOKIE_PARAMS = dict(
    secure=True,
    samesite="None",
    domain=".tds-dossier.fr",
    path="/",
)


class LoginView(APIView):
    """
    Vue API pour l’authentification d’un utilisateur.
    Pose les cookies HttpOnly pour access et refresh tokens.
    Ne pose **plus** de cookie pour le rôle.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = serializer.validated_data["tokens"]

        # 🕐 Optionnel : mise à jour du last_login
        update_last_login(User, user)


        # 🔐 Cookies JWT HttpOnly
        response.set_cookie(
            key="access_token",
            value=tokens["access"],
            httponly=True,
            max_age=60 * 60,
            **COMMON_COOKIE_PARAMS,
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            max_age=60 * 60 * 24 * 7,
            **COMMON_COOKIE_PARAMS,
        )

        return response


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    """
    Vue API pour la déconnexion de l'utilisateur.
    Supprime les cookies JWT (access_token et refresh_token).
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)

        response.delete_cookie("access_token", **COMMON_COOKIE_PARAMS)
        response.delete_cookie("refresh_token", **COMMON_COOKIE_PARAMS)

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Vue personnalisée qui lit le refresh_token depuis les cookies HttpOnly
    et renvoie un nouveau access_token dans un cookie.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Missing refresh token in cookies"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and "access" in response.data:
            access_token = response.data["access"]

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                max_age=60 * 60,
                **COMMON_COOKIE_PARAMS,
            )

            # Optionnel : tu peux masquer le token dans le body si nécessaire
            # del response.data["access"]

        return response