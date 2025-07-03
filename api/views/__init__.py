from .auth_views import LoginView
from .email_form_views import SendFormulaireEmailView
from .lead_views import LeadViewSet
from .client_views import ClientViewSet
from .comment_views import CommentViewSet
from .user_views import UserViewSet
from .document_view import DocumentViewSet
from .document_download_view import DocumentDownloadView
from .user_avatar_views import UserAvatarSerializer
from .contract_views import ContractViewSet
from .service_views import ServiceViewSet
from .Lead_status_view import LeadStatusViewSet
from .status_dossier_view import StatusDossierViewSet

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
    "ContractViewSet",
    "ServiceViewSet",
    "LeadStatusViewSet",
    "StatusDossierViewSet",
]

