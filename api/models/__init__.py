from .user import User, CustomUserManager
from .role import Role
from .client import Client
from .lead import Lead, LeadStatus
from .comment import Comment

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

    # Roles
    'Role',

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
]