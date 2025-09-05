from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.core import signing
from django.shortcuts import redirect

from api.custom_auth.serializers import LoginSerializer

User = get_user_model()
IS_HTTPS = not settings.DEBUG

# 🔐 Paramètres communs pour les cookies
COMMON_COOKIE_PARAMS = dict(
    secure=True,
    samesite="None",
    domain=".tds-dossier.fr",
    path="/",
)

# 🔐 Salt spécifique pour la signature du rôle
USER_ROLE_SALT = "user_role_cookie"


class LoginView(APIView):
    """
    Vue API pour l’authentification d’un utilisateur.
    Pose les cookies JWT (HttpOnly) et renvoie un 200 avec le rôle dans le body.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(
                data=request.data,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)

            user = serializer.validated_data["user"]
            tokens = serializer.validated_data["tokens"]

            update_last_login(User, user)

            response = Response(
                {
                    "detail": "Login successful",
                    "role": user.role,
                    "role_display": user.get_role_display(),
                },
                status=status.HTTP_200_OK,
            )

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

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    """
    Vue API pour la déconnexion.
    Supprime les cookies access_token, refresh_token, user_role.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access_token", **COMMON_COOKIE_PARAMS)
        response.delete_cookie("refresh_token", **COMMON_COOKIE_PARAMS)
        response.delete_cookie("user_role", **COMMON_COOKIE_PARAMS)  # 🧹 important
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Rafraîchit le token d’accès en lisant le refresh_token depuis les cookies HttpOnly.
    Renvoie un nouveau access_token uniquement dans le cookie.
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

            del response.data["access"]

        return response