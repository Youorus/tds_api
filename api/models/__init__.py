from .user import User, CustomUserManager
from .client import Client
from .lead import Lead, LeadStatus
from .comment import Comment
from .document import Document

# Enums & choices
from .client import (
    SourceInformation,
    Civilite,
    VisaType,
    TypeDemande,
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
    'TypeDemande',
    'SituationFamiliale',
    'LogementType',
    'SituationProfessionnelle',

    # Comments
    'Comment',
    'Document'
]