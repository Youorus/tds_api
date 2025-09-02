from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from api.custom_auth.serializers import LoginSerializer

User = get_user_model()

from django.conf import settings

IS_HTTPS = not settings.DEBUG  # Utilise HTTPS en dehors du mode debug


class LoginView(APIView):
    """
    Vue API pour l’authentification d’un utilisateur.
    Pose les cookies HttpOnly pour access et refresh tokens.
    Renvoie uniquement le rôle dans le body.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = serializer.validated_data["tokens"]

        # 🔄 Optionnel : mise à jour du last_login
        update_last_login(User, user)

        response = Response(
            data={
                "role": user.role,
                "role_display": user.get_role_display(),
            },
            status=status.HTTP_200_OK,
        )

        # 🔐 Cookies HttpOnly
        response.set_cookie(
            key="access_token",
            value=tokens["access"],
            httponly=True,
            secure=IS_HTTPS,
            samesite="Lax",
            path="/",
            max_age=60 * 60,  # 1 heure
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            secure=IS_HTTPS,
            samesite="Lax",
            path="/",
            max_age=60 * 60 * 24 * 7,  # 7 jours
        )

        # ✅ Cookie non-HttpOnly pour usage frontend (redirection, affichage rapide, etc.)
        response.set_cookie(
            key="user_role",
            value=user.role,
            httponly=False,
            secure=IS_HTTPS,
            samesite="Lax",
            path="/",
            max_age=60 * 60 * 24 * 7,
        )

        return response


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    """
    Vue API pour la déconnexion de l'utilisateur.
    Supprime les cookies JWT (access_token et refresh_token).
    Exempte la vue de la vérification CSRF (cookies HttpOnly déjà sécurisés).
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)

        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        response.delete_cookie("user_role", path="/")

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Vue personnalisée qui lit le refresh_token depuis les cookies HttpOnly
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        print("🔁 refresh_token from cookie:", refresh_token)

        if not refresh_token:
            return Response(
                {"detail": "Missing refresh token in cookies"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🧠 Injecte le token dans request.data
        request.data["refresh"] = refresh_token

        # Appelle la vue parent avec le body modifié
        response = super().post(request, *args, **kwargs)

        # Ajoute access_token en cookie s’il est là
        if response.status_code == 200 and "access" in response.data:
            access_token = response.data["access"]
            from django.conf import settings

            IS_HTTPS = not settings.DEBUG

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=IS_HTTPS,
                samesite="Lax",
                path="/",
                max_age=60 * 60,  # 1 heure
            )

            # Optionnel : retire le token du body
            # del response.data["access"]

        return response
