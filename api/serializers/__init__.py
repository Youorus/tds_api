from rest_framework import serializers
from django.contrib.auth import get_user_model
from .user_serializers import UserSerializer, LoginSerializer
from .role_serializers import RoleSerializer
from .client_serializers import ClientSerializer
from .lead_serializers import LeadSerializer
from .comment_serializers import CommentSerializer

User = get_user_model()

__all__ = [
    "UserSerializer",
    "LoginSerializer",
    "RoleSerializer",
    "ClientSerializer",
    "LeadSerializer",
    "CommentSerializer",
]  # Facilite l'import dans d'autres modules
