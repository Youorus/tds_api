from .auth_views import LoginView
from .email_form_views import SendFormulaireEmailView
from .lead_views import LeadViewSet
from .client_views import ClientViewSet
from .comment_views import CommentViewSet
from .user_views import UserViewSet
from .document_view import DocumentViewSet
from .document_download_view import DocumentDownloadView
from .user_avatar_views import UserAvatarSerializer
from .payment_views import PaymentViewSet

__all__ = [
    "LoginView",
    "UserViewSet",
    "LeadViewSet",
    "ClientViewSet",
    "CommentViewSet",
    "SendFormulaireEmailView",
    "DocumentViewSet",
    "DocumentDownloadView",
    "UserAvatarSerializer",
    "PaymentViewSet",
]

