from django.db import models
from django.utils.translation import gettext_lazy as _

class LeadStatus(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    color = models.CharField(max_length=10, default="#333333")

    class Meta:
        verbose_name = _('statut de lead')
        verbose_name_plural = _('statuts de lead')
        ordering = ["label"]

    def __str__(self):
        return f"{self.label}"