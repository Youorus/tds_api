from django.db import models
from django.utils.translation import gettext_lazy as _

class StatutDossier(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name=_('code'))
    label = models.CharField(max_length=100, verbose_name=_('nom affiché'))
    color = models.CharField(max_length=10, default="#4b5563", verbose_name=_('couleur (hexa)'))

    class Meta:
        verbose_name = _('statut dossier')
        verbose_name_plural = _('statuts dossier')
        ordering = ["label"]

    def __str__(self):
        return f"{self.label} ({self.code})"