from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMode(models.TextChoices):
    ESPECES = "ESPECES", _("Espèces")
    CB = "CB", _("Carte bancaire")
    VIREMENT = "VIREMENT", _("Virement bancaire")
    CHEQUE = "CHEQUE", _("Chèque")
    PNF = "PNF", _("Crédit Cofidis (PNF)")
    PAYPAL = "PAYPAL", _("PayPal")
    STRIPE = "STRIPE", _("Stripe")
    KLARNA = "KLARNA", _("Klarna")
    SCLP = "SCLP", _("Scalapay")  # si c’est bien ça
    AUTRE = "AUTRE", _("Autre / Non spécifié")