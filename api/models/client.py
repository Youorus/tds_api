from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _


# --- ENUMS ---

class SourceInformation(models.TextChoices):
    GOOGLE = 'GOOGLE', _('Google')
    FACEBOOK = 'FACEBOOK', _('Facebook')
    INSTAGRAM = 'INSTAGRAM', _('Instagram')
    TIKTOK = 'TIKTOK', _('Tiktok')
    PASSAGE = 'PASSAGE', _('Passage')
    PUB_METRO = 'PUB_METRO', _('Pub métro')
    BOUCHE_OREILLE = 'BOUCHE_OREILLE', _('Bouche à oreille')
    FLYERS = 'FLYERS', _('Flyers')
    TV = 'TV', _('TV')
    RADIO = 'RADIO', _('Radio')
    AUTRES = 'AUTRES', _('Autres (précisez)')


class Civilite(models.TextChoices):
    MADAME = 'MADAME', _('Madame')
    MADEMOISELLE = 'MADEMOISELLE', _('Mademoiselle')
    MONSIEUR = 'MONSIEUR', _('Monsieur')


class VisaType(models.TextChoices):
    SCHENGEN = 'SCHENGEN', _('Visa Schengen')
    LONG_SEJOUR = 'LONG_SEJOUR', _('Visa long séjour')
    ETUDIANT = 'ETUDIANT', _('Visa étudiant')
    VLS_TS = 'VLS_TS', _('VLS-TS')
    AUTRE = 'AUTRE', _('Autre')


class TypeDemande(models.TextChoices):
    TITRE_SEJOUR = 'TITRE_SEJOUR', _('Titre de séjour (1ère demande)')
    RENOUVELLEMENT = 'RENOUVELLEMENT', _('Renouvellement titre de séjour')
    NATURALISATION = 'NATURALISATION', _('Naturalisation')
    DEMANDE_VISA = 'DEMANDE_VISA', _('Demande de visa')
    REGROUPEMENT_FAMILIAL = 'REGROUPEMENT_FAMILIAL', _('Regroupement familial')
    CONTESTATION_OQTF = 'CONTESTATION_OQTF', _('Contestation OQTF')
    SUIVI_DOSSIER = 'SUIVI_DOSSIER', _('Suivi de dossier')
    PRISE_RDV = 'PRISE_RDV', _('Prise de rendez-vous')
    AUTRES = 'AUTRES', _('Autres (précisez)')


class SituationFamiliale(models.TextChoices):
    CELIBATAIRE = 'CELIBATAIRE', _('Célibataire')
    MARIE = 'MARIE', _('Marié(e)')
    CONCUBIN = 'CONCUBIN', _('Concubin(e)')
    DIVORCE = 'DIVORCE', _('Divorcé(e)')
    VEUF = 'VEUF', _('Veuf(ve)')


class LogementType(models.TextChoices):
    LOCATAIRE = 'LOCATAIRE', _('Locataire')
    PROPRIETAIRE = 'PROPRIETAIRE', _('Propriétaire')
    HEBERGE = 'HEBERGE', _('Hébergé')
    AUTRE = 'AUTRE', _('Autre')


class SituationProfessionnelle(models.TextChoices):
    CDI = 'CDI', _('En CDI')
    CDD_INTERIM = 'CDD_INTERIM', _('En CDD / Intérim')
    INDEPENDANT = 'INDEPENDANT', _('Profession libérale / Indépendant')
    ETUDIANT = 'ETUDIANT', _('Étudiant')
    SANS_EMPLOI = 'SANS_EMPLOI', _('Sans emploi')


# --- MODEL ---

class Client(models.Model):
    lead = models.OneToOneField('Lead', on_delete=models.CASCADE, related_name='form_data')

    source = ArrayField(
        models.CharField(max_length=30, choices=SourceInformation.choices),
        verbose_name=_('source'),
        default=list,
        blank=True
    )

    civilite = models.CharField(_('civilité'), max_length=15, choices=Civilite.choices, blank=True)

    date_naissance = models.DateField(_('date de naissance'), blank=True, null=True)
    lieu_naissance = models.CharField(_('lieu de naissance'), max_length=255, blank=True)
    pays = models.CharField(_('pays'), max_length=100, blank=True)
    nationalite = models.CharField(_('nationalité'), max_length=100, blank=True)

    adresse = models.CharField(_('adresse'), max_length=255, blank=True)
    code_postal = models.CharField(_('code postal'), max_length=20, blank=True)
    ville = models.CharField(_('ville'), max_length=100, blank=True)
    date_entree_france = models.DateField(_('date d’entrée en France'), blank=True, null=True)

    a_un_visa = models.BooleanField(_('visa'), null=True, blank=True)
    type_visa = models.CharField(_('type de visa'), null=True, max_length=20, choices=VisaType.choices, blank=True)
    statut_refugie_ou_protection = models.BooleanField(_('statut réfugié ou protection subsidiaire'), null=True, blank=True)

    types_demande = ArrayField(
        models.CharField(max_length=30, choices=TypeDemande.choices),
        verbose_name=_('types de demande'),
        default=list,
        blank=True
    )
    demande_deja_formulee = models.BooleanField(_('demande déjà formulée ?'), null=True, blank=True)
    demande_formulee_precise = models.CharField(_('si oui, laquelle ?'), max_length=255, blank=True)

    situation_familiale = models.CharField(_('situation familiale'), max_length=20, choices=SituationFamiliale.choices, blank=True)
    a_des_enfants = models.BooleanField(_('a des enfants ?'), null=True, blank=True)
    nombre_enfants = models.PositiveIntegerField(_('nombre d’enfants'), blank=True, null=True)
    nombre_enfants_francais = models.PositiveIntegerField(_('nombre d’enfants français'), blank=True, null=True)
    enfants_scolarises = models.BooleanField(_('enfants scolarisés ?'), null=True, blank=True)
    naissance_enfants_details = models.TextField(_('détails naissance enfants'), blank=True)

    situation_pro = models.CharField(_('situation professionnelle'), max_length=30, choices=SituationProfessionnelle.choices, blank=True)
    domaine_activite = models.CharField(_('domaine d’activité'), max_length=255, blank=True)
    nombre_fiches_paie = models.PositiveIntegerField(_('nombre de fiches de paie'), blank=True, null=True)
    date_depuis_sans_emploi = models.DateField(_('depuis quelle date sans emploi / étudiant'), blank=True, null=True)

    a_deja_eu_oqtf = models.BooleanField(_('déjà eu une OQTF ?'), null=True, blank=True)
    date_derniere_oqtf = models.DateField(_('date de la dernière OQTF'), null=True, blank=True)
    demarche_en_cours_administration = models.BooleanField(_('démarche en cours auprès de l’administration ?'), null=True, blank=True)

    remarques = models.TextField(_('remarques'), blank=True)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('données client')
        verbose_name_plural = _('données clients')
        ordering = ['-created_at']

    def __str__(self):
        return f"Données de {self.lead.first_name} {self.lead.last_name}"