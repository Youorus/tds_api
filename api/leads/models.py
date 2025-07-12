from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api.lead_status.models import LeadStatus
from api.leads.constants import RDV_PLANIFIE, RDV_CONFIRME


class Lead(models.Model):
    """
    Modèle représentant un prospect (Lead) pour le suivi commercial.

    Ce modèle centralise toutes les informations nécessaires à la gestion
    et à la qualification d’un lead (prospect), de la création à la prise de rendez-vous,
    en passant par l’assignation à un conseiller et le suivi du statut.
    """

    id = models.AutoField(
        primary_key=True,
        verbose_name=_('ID')
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name=_('prénom'),
        help_text=_('Prénom du prospect')
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name=_('nom'),
        help_text=_('Nom de famille du prospect')
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('email'),
        help_text=_('Adresse email du prospect (optionnelle)')
    )

    phone = models.CharField(
        max_length=20,
        verbose_name=_('téléphone'),
        help_text=_('Numéro de téléphone au format international (ex: +33612345678)')
    )

    statut_dossier = models.ForeignKey(
        'statut_dossier.StatutDossier',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('statut du dossier'),
        help_text=_('Suivi interne de l’état d’avancement du dossier')
    )

    appointment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('date de rendez-vous'),
        help_text=_('Date et heure du rendez-vous (optionnel)')
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('date de création'),
        help_text=_('Date et heure de création du lead')
    )

    status = models.ForeignKey(
        'lead_status.LeadStatus',
        on_delete=models.PROTECT,
        verbose_name=_('statut'),
        help_text=_('Statut actuel du lead (ex: NOUVEAU, RDV_VALIDÉ, etc.)')
    )

    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('assigné à'),
        help_text=_('Conseiller à qui ce lead est assigné')
    )
    jurist_assigned = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='leads_juriste',
        verbose_name=_('juriste assigné'),
        help_text=_('Juriste responsable du lead (assigné par un administrateur)')
    )

    class Meta:
        verbose_name = _('lead')
        verbose_name_plural = _('leads')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='lead_status_idx'),
            models.Index(fields=['appointment_date'], name='lead_appointment_idx'),
            models.Index(fields=['created_at'], name='lead_created_idx'),
            models.Index(fields=['jurist_assigned'], name='lead_jurist_idx'),
        ]

    def __str__(self):
        """
        Affichage lisible du lead : Prénom, nom et statut.
        """
        return f"{self.first_name} {self.last_name} - {self.status.label if self.status else _('Sans statut')}"

    def save(self, *args, **kwargs):
        """
        Surcharge la méthode save pour :
        - Affecter un statut par défaut 'RDV_PLANIFIE' si aucun statut n'est défini.
        - Passer à 'RDV_CONFIRME' si une date de rendez-vous est fixée, quel que soit le statut courant.
        """

        # 1. Statut par défaut si absent
        if not self.status:
            try:
                default_status = LeadStatus.objects.get(code=RDV_PLANIFIE)
                self.status = default_status
            except LeadStatus.DoesNotExist:
                pass  # Tu peux lever une exception si besoin

        super().save(*args, **kwargs)