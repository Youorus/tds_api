from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core import signing
from django.conf import settings

from .serializers import UserSerializer

# Même sel que dans LoginView
USER_ROLE_SALT = "user_role_cookie"


class MeView(APIView):
    """
    Vue API qui retourne les informations de l'utilisateur connecté,
    ainsi que son rôle vérifié depuis le cookie signé.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Décodage sécurisé du rôle signé
            signed_role = request.COOKIES.get("user_role")
            role = signing.loads(signed_role, salt=USER_ROLE_SALT)
        except Exception:
            return Response(
                {"detail": "Cookie 'user_role' invalide ou manquant."},
                status=400
            )

        serializer = UserSerializer(request.user, context={"request": request})

        return Response({
            "user": serializer.data,
            "role": role,  # ← rôle validé cryptographiquement
        })