import unicodedata
from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
import re

class Service(models.Model):
    """
    Modèle représentant un service proposé au client
    (ex: Titre de séjour, Naturalisation, etc.).

    Attributs :
        - code : Code unique, en MAJUSCULES et sans espace (ex: "TITRE_SEJOUR")
        - label : Libellé lisible pour l'utilisateur (ex: "Titre de séjour")
        - price : Tarif affiché du service (décimal, par défaut 0.00)
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Code du service"),
        help_text=_("Code interne unique du service (ex: NATURALISATION, TITRE_SEJOUR)")
    )
    label = models.CharField(
        max_length=1000,
        verbose_name=_("Libellé"),
        help_text=_("Nom lisible du service (ex: Titre de séjour)")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Prix (€)"),
        help_text=_("Tarif affiché pour ce service")
    )

    class Meta:
        verbose_name = _("service")
        verbose_name_plural = _("services")
        ordering = ["label"]
        indexes = [
            models.Index(fields=["code"], name="service_code_idx"),
            models.Index(fields=["label"], name="service_label_idx"),
        ]

    def __str__(self):
        """
        Affichage lisible du service (ex: 'Titre de séjour (120.00 €)')
        """
        return f"{self.label} ({self.price} €)"

    def clean_code(self, code):
        """
        Nettoie et normalise le code :
        - Supprime espaces/tirets/underscores
        - Met en MAJUSCULES
        - Supprime les accents
        - Trim début/fin
        """
        code = code.strip()
        # Supprime les accents
        code = ''.join(
            c for c in unicodedata.normalize('NFD', code)
            if unicodedata.category(c) != 'Mn'
        )
        code = code.replace(" ", "").replace("_", "").replace("-", "")
        code = code.upper()
        return code

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.clean_code(self.code)
        super().save(*args, **kwargs)