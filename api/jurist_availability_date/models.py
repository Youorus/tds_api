# test_models.py

from django.db import models


class JuristGlobalAvailability(models.Model):
    """
    Définit les créneaux globaux où il est possible de prendre RDV avec un juriste,
    indépendamment de la personne.
    """

    DAYS_OF_WEEK = [
        (0, "Lundi"),
        (1, "Mardi"),
        (2, "Mercredi"),
        (3, "Jeudi"),
        (4, "Vendredi"),
        (5, "Samedi"),
        (6, "Dimanche"),
    ]
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("day_of_week", "start_time", "end_time")
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return (
            f"{self.get_day_of_week_display()} de "
            f"{self.start_time.strftime('%H:%M')} à {self.end_time.strftime('%H:%M')}"
        )
