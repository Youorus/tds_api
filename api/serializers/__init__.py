from django.contrib.auth import get_user_model

from .lead_status import LeadStatusUpdateSerializer
from .login_serializer import LoginSerializer
from .user_serializers import UserSerializer, PasswordChangeSerializer
from .client_serializers import ClientSerializer
from .lead_serializers import LeadSerializer
from .comment_serializers import CommentSerializer

User = get_user_model()

__all__ = [
    "UserSerializer",
    "LoginSerializer",
    "ClientSerializer",
    "LeadSerializer",
    "LeadStatusUpdateSerializer",
    "CommentSerializer",
    "PasswordChangeSerializer",
]  # Facilite l'import dans d'autres modules
