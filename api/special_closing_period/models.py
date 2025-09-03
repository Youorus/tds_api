# models/special_closing_period.py

from django.db import models


class SpecialClosingPeriod(models.Model):
    """
    Période de fermeture exceptionnelle (jours fériés, vacances, fermeture ponctuelle).
    La période inclut start_date et end_date (bornes inclusives).
    """

    label = models.CharField(
        max_length=100,
        help_text="Nom ou motif de la fermeture (ex : 'Noël', 'Vacances d'été', 'Travaux', etc.)",
    )
    start_date = models.DateField(help_text="Premier jour fermé (inclusif)")
    end_date = models.DateField(help_text="Dernier jour fermé (inclusif)")

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Fermeture exceptionnelle"
        verbose_name_plural = "Fermetures exceptionnelles"

    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.label} : {self.start_date.strftime('%d/%m/%Y')}"
        return f"{self.label} : du {self.start_date.strftime('%d/%m/%Y')} au {self.end_date.strftime('%d/%m/%Y')}"
