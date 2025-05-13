from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class LeadStatus(models.TextChoices):
    NOUVEAU = 'NOUVEAU', _('Nouveau')
    NRP = 'NRP', _('NRP')
    NRP_PLUS = 'NRP++', _('NRP ++')
    NRP_MESSAGE = 'NRP+MESSAGE', _('NRP+MESSAGE')
    CLIENT_RAPPELLERA = 'CLIENT_RAPPELLERA', _('Client rappellera')
    PRESENT = 'PRESENT', _('Présent')
    PAYE = 'PAYE', _('Payé')
    DOSS_EN_COURS = 'DOSS_EN_COURS', _('Dossier en cours')
    FAUX_NUMERO = 'FAUX_NUMERO', _('Faux numéro')
    PAS_INTERRESSE = 'PAS_INTERRESSE', _('Pas intéressé')
    RDV_PLANIFIER = 'RDV_PLANIFIER', _('Rendez-vous planifié')
    RDV_CONFIRME = 'RDV_CONFIRME', _('Rendez-vous confirmé')
    ATTENTE_REGLEMENT = 'ATTENTE_REGLEMENT', _('Attente règlement')
    FORMULAIRE_OK = 'FORMULAIRE_OK', _('Formulaire OK')
    ANNULE = 'ANNULE', _('Annulé')
    ELLIGIBLE = 'ELLIGIBLE', _('Eligible')
    PAS_DE_REPONSE = 'PAS_DE_REPONSE', _('Pas de réponse')
    SOUCIS_FINANCIER = 'SOUCIS_FINANCIER', _('Soucis financier')
    DIFFICULTE_FINANCIERE = 'DIFFICULTE_FINANCIERE', _('Difficulté financière')
    ABSENT = 'ABSENT', _('Absent')
    REVIENDRA = 'REVIENDRA', _('Reviendra')
    A_RAPPELER = 'A_RAPPELER', _('A rappeler')
    PIECES_MANQUANTES = 'PIECES_MANQUANTES', _('Pièce(s) manquante(s)')

class StatutDossier(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", _("En attente")
    INCOMPLET = "INCOMPLET", _("Incomplet")
    COMPLET = "COMPLET", _("Complet")
    A_VERIFIER = "A_VERIFIER", _("À vérifier")
    EN_COURS_INSTRUCTION = "EN_COURS_INSTRUCTION", _("En cours d’instruction")
    RDV_PRIS = "RDV_PRIS", _("Rendez-vous pris")
    RDV_EFFECTUE = "RDV_EFFECTUE", _("Rendez-vous effectué")
    VALIDE = "VALIDE", _("Validé")
    REFUSE = "REFUSE", _("Refusé")
    ABANDONNE = "ABANDONNE", _("Abandonné")
    ANNULE = "ANNULE", _("Annulé")
    ARCHIVE = "ARCHIVE", _("Archivé")


class Lead(models.Model):
    """
    Modèle représentant un prospect (lead) avec toutes les informations nécessaires
    pour le suivi commercial.
    """

    id = models.AutoField(
        primary_key=True,
        verbose_name=_('ID')
    )

    first_name = models.CharField(
        _('prénom'),
        max_length=150,
        help_text=_('Prénom du prospect')
    )

    last_name = models.CharField(
        _('nom'),
        max_length=150,
        help_text=_('Nom de famille du prospect')
    )

    email = models.EmailField(
        _('email'),
        blank=True,
        null=True,
        help_text=_('Adresse email du prospect (optionnelle)')
    )

    phone = models.CharField(
        _('téléphone'),
        max_length=20,
        help_text=_('Numéro de téléphone au format international (ex: +33612345678)')
    )

    statut_dossier = models.CharField(
        _('statut du dossier'),
        max_length=30,
        choices=StatutDossier.choices,
        blank=True,
        null=True,
        help_text=_('Suivi interne de l’état d’avancement du dossier')
    )

    appointment_date = models.DateTimeField(
        _('date de rendez-vous'),
        blank=True,
        null=True,
        help_text=_('Date et heure du rendez-vous (optionnel)')
    )

    created_at = models.DateTimeField(
        _('date de création'),
        default=timezone.now,
        help_text=_('Date et heure de création du lead')
    )

    status = models.CharField(
        _('statut'),
        max_length=30,
        choices=LeadStatus.choices,
        default=LeadStatus.NOUVEAU,
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
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour définir automatiquement le statut"""
        if self.appointment_date and self.status == LeadStatus.NOUVEAU:
            self.status = LeadStatus.RDV_CONFIRME
        super().save(*args, **kwargs)