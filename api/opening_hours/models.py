from django.db import models

class OpeningHours(models.Model):
    DAY_CHOICES = [
        (0, "Lundi"),
        (1, "Mardi"),
        (2, "Mercredi"),
        (3, "Jeudi"),
        (4, "Vendredi"),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    open_time = models.TimeField(null=True, blank=True, help_text="Heure d'ouverture (laisser vide = fermé)")
    close_time = models.TimeField(null=True, blank=True, help_text="Heure de fermeture (laisser vide = fermé)")

    class Meta:
        ordering = ["day_of_week"]
        verbose_name = "Horaire d'ouverture"
        verbose_name_plural = "Horaires d'ouverture"

    def __str__(self):
        if self.open_time and self.close_time:
            return f"{self.get_day_of_week_display()}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"
        return f"{self.get_day_of_week_display()}: Fermé"

    @property
    def is_closed(self):
        return not (self.open_time and self.close_time)