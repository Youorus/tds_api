from django.db import models
from django.utils.translation import gettext_lazy as _

class PaymentMode(models.TextChoices):
    ESPECES = "ESPECES", _("Espèces")
    CB = "CB", _("Carte bancaire")
    VIREMENT = "VIREMENT", _("Virement")
    CHEQUE = "CHEQUE", _("Chèque")
    PNF = "PNF", _("Crédit Cofidis (PNF)")