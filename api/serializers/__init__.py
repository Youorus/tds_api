# api/serializers/__init__.py

from django.contrib.auth import get_user_model

# Import de tous les serializers
from .lead_status import LeadStatusUpdateSerializer
from .login_serializer import LoginSerializer
from .user_serializers import UserSerializer, PasswordChangeSerializer
from .client_serializers import ClientSerializer
from .lead_serializers import LeadSerializer
from .comment_serializers import CommentSerializer
from .document_serializer import DocumentSerializer
from .user_avatar_serializer import UserAvatarSerializer
from .payment_serializers import PaymentSerializer, PaymentReceiptSerializer

User = get_user_model()

__all__ = [
    "UserSerializer",
    "LoginSerializer",
    "ClientSerializer",
    "LeadSerializer",
    "LeadStatusUpdateSerializer",
    "CommentSerializer",
    "DocumentSerializer",
    "PasswordChangeSerializer",
    "UserAvatarSerializer",
    "PaymentSerializer",
    "PaymentReceiptSerializer",
]