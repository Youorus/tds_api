from .auth_views import LoginView
from .email_form_views import SendFormulaireEmailView
from .lead_views import LeadViewSet
from .client_views import ClientViewSet
from .comment_views import CommentViewSet
from .user_views import UserViewSet

__all__ = [
    "LoginView",
    "UserViewSet",
    "LeadViewSet",
    "ClientViewSet",
    "CommentViewSet",
    "SendFormulaireEmailView",
]

