from django.db import models
from django.utils import timezone


class JuristGlobalAvailability(models.Model):
    """
    Définit les créneaux globaux où il est possible de prendre rendez-vous
    avec un juriste, indépendamment d’une personne.
    """

    date = models.DateField(
        default=timezone.now,
        help_text="Date du créneau de disponibilité."
    )
    start_time = models.TimeField(
        help_text="Heure de début du créneau (HH:MM)."
    )
    end_time = models.TimeField(
        help_text="Heure de fin du créneau (HH:MM)."
    )
    repeat_weekly = models.BooleanField(
        default=False,
        help_text="Si coché, ce créneau est répété chaque semaine au même jour de semaine."
    )

    class Meta:
        verbose_name = "Disponibilité globale juriste"
        verbose_name_plural = "Disponibilités globales juristes"
        ordering = ["date", "start_time"]
        unique_together = ("date", "start_time", "end_time")

    def __str__(self) -> str:
        base_str = (
            f"{self.date.strftime('%d/%m/%Y')} "
            f"de {self.start_time.strftime('%H:%M')} "
            f"à {self.end_time.strftime('%H:%M')}"
        )
        if self.repeat_weekly:
            base_str += " (répété chaque semaine)"
        return base_str