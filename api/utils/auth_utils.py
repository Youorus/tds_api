# api/utils/auth_utils.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.conf import settings


def get_user_id_from_cookie(request):
    """
    Récupère l'ID utilisateur à partir du token JWT dans les cookies
    Args:
        request: Objet HttpRequest
    Returns:
        int: ID de l'utilisateur ou None si non authentifié/invalide
    """
    access_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'])

    if not access_token:
        return None

    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(access_token)
        user = jwt_auth.get_user(validated_token)
        return user.id
    except (InvalidToken, AuthenticationFailed):
        return None