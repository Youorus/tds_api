from rest_framework import serializers
from django.contrib.auth import get_user_model

from .lead_status import LeadStatusUpdateSerializer
from .login_serializer import LoginSerializer
from .user_serializers import UserSerializer
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
    "LeadStatusUpdateSerializer",
    "CommentSerializer",
]  # Facilite l'import dans d'autres modules
