from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Lead(models.Model):
    """
    Modèle représentant un prospect (lead) avec toutes les informations nécessaires
    pour le suivi commercial.
    """
    id = models.AutoField(primary_key=True, verbose_name=_('ID'))

    first_name = models.CharField(
        _('prénom'), max_length=150,
        help_text=_('Prénom du prospect')
    )

    last_name = models.CharField(
        _('nom'), max_length=150,
        help_text=_('Nom de famille du prospect')
    )

    email = models.EmailField(
        _('email'), blank=True, null=True,
        help_text=_('Adresse email du prospect (optionnelle)')
    )

    phone = models.CharField(
        _('téléphone'), max_length=20,
        help_text=_('Numéro de téléphone au format international (ex: +33612345678)')
    )

    statut_dossier = models.ForeignKey(
        'StatutDossier',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('statut du dossier'),
        help_text=_('Suivi interne de l’état d’avancement du dossier')
    )

    appointment_date = models.DateTimeField(
        _('date de rendez-vous'), blank=True, null=True,
        help_text=_('Date et heure du rendez-vous (optionnel)')
    )

    created_at = models.DateTimeField(
        _('date de création'), default=timezone.now,
        help_text=_('Date et heure de création du lead')
    )

    status = models.ForeignKey(
        'LeadStatus',
        on_delete=models.PROTECT,
        verbose_name=_('statut'),
        help_text=_('Statut actuel du lead')
    )

    assigned_to = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('assigné à'),
        help_text=_('Conseiller à qui ce lead est assigné')
    )

    class Meta:
        verbose_name = _('lead')
        verbose_name_plural = _('leads')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='lead_status_idx'),
            models.Index(fields=['appointment_date'], name='lead_appointment_idx'),
            models.Index(fields=['created_at'], name='lead_created_idx'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status.label if self.status else 'Sans statut'}"

    def save(self, *args, **kwargs):
        """
        Met automatiquement le statut à 'RDV_CONFIRMÉ' si un rendez-vous est défini
        et que le statut actuel est 'NOUVEAU'.
        """
        if self.appointment_date and self.status and self.status.label.upper() == "NOUVEAU":
            try:
                from api.models import LeadStatus
                rdv_confirme = LeadStatus.objects.get(label__iexact="RDV_VALIDÉ")
                self.status = rdv_confirme
            except LeadStatus.DoesNotExist:
                pass  # On ne fait rien si le statut n'existe pas
        super().save(*args, **kwargs)
