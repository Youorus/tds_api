from .payment import Payment
from .user import User, CustomUserManager
from .client import Client
from .lead import Lead, LeadStatus, StatutDossier
from .comment import Comment
from .document import Document
from .PaymentReceipt import PaymentReceipt
from .payment import Payment

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
    'Payment',
    'PaymentReceipt'
]