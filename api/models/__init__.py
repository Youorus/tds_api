from .user import User, CustomUserManager
from .client import Client
from .lead import Lead
from .comment import Comment
from .document import Document
from .PaymentReceipt import PaymentReceipt
from .Contract import Contract
from .services import Service
from .lead_status import LeadStatus
from .statut_dossier import StatutDossier



# Enums & choices
from .client import (
    SourceInformation,
    Civilite,
    VisaType,
    SituationFamiliale,
    LogementType,
    SituationProfessionnelle,
)

__all__ = [
    # Users
    'User',
    'CustomUserManager',

    # Leads
    'Lead',
    'LeadStatus',

    # Clients
    'Client',
    'SourceInformation',
    'Civilite',
    'VisaType',
    'SituationFamiliale',
    'LogementType',
    'SituationProfessionnelle',

    # Comments
    'Comment',
    'Document',
    'PaymentReceipt',
    'Contract',
    'Service',
    'StatutDossier'
]