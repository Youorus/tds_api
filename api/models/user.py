import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User.
    Implémente les méthodes nécessaires à la création d'utilisateurs et super-utilisateurs.
    """

    def create_user(self, email, first_name, last_name, password=None, role="COMMERCIAL", **extra_fields):
        if not email:
            raise ValueError(_('L\'email doit être renseigné'))
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **extra_fields
        )

        # Gestion staff/superuser selon le rôle
        if role == User.Roles.ADMIN:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = True  # Pour tous les rôles internes, tu peux adapter selon ton besoin
            user.is_superuser = False

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Roles.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le super-utilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le super-utilisateur doit avoir is_superuser=True.'))

        return self.create_user(email, first_name, last_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé remplaçant le modèle User par défaut de Django.
    Utilise l'email comme identifiant principal et UUID comme clé primaire.
    """

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", _("Administrateur")
        ACCUEIL = "ACCUEIL", _("Accueil")
        JURISTE = "JURISTE", _("Juriste")
        CONSEILLER = "CONSEILLER", _("Conseiller")
        COMPTABILITE = "COMPTABILITE", _("Comptabilité")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID unique'),
        help_text=_('Identifiant universel unique (UUIDv4)')
    )

    email = models.EmailField(
        _('adresse email'),
        unique=True,
        error_messages={
            'unique': _("Un compte existe déjà avec cet email.")
        },
        help_text=_('Adresse email utilisée comme identifiant de connexion')
    )

    first_name = models.CharField(
        _('prénom'),
        max_length=150,
        blank=False,
        help_text=_('Prénom de l\'utilisateur (requis)')
    )

    last_name = models.CharField(
        _('nom'),
        max_length=150,
        blank=False,
        help_text=_('Nom de famille de l\'utilisateur (requis)')
    )

    role = models.CharField(
        _('rôle'),
        max_length=32,
        default=Roles.CONSEILLER,
        choices=Roles.choices,
        help_text=_("Rôle du collaborateur")
    )

    is_staff = models.BooleanField(
        _('membre du staff'),
        default=False,
        help_text=_('Détermine si l\'utilisateur peut accéder à l\'interface d\'administration')
    )

    is_superuser = models.BooleanField(
        _('super-utilisateur'),
        default=False,
        help_text=_('Détermine si l\'utilisateur a toutes les permissions sans attribution explicite')
    )

    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_(
            'Désigne si ce compte doit être considéré comme actif. Désélectionnez cette option plutôt que de supprimer le compte.')
    )

    date_joined = models.DateTimeField(
        _('date d\'inscription'),
        auto_now_add=True,
        help_text=_('Date et heure de création du compte')
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['date_joined'], name='date_joined_idx'),
        ]

    def __str__(self):
        """Représentation textuelle de l'utilisateur (email + nom complet)"""
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        """Retourne le prénom de l'utilisateur"""
        return self.first_name

    # (Optionnel) Si tu veux synchroniser staff/superuser/role à chaque save :
    def save(self, *args, **kwargs):
        if self.role == self.Roles.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = True  # tu peux adapter (ex: self.role in ["ADMIN", "SUPPORT", ...])
            self.is_superuser = False
        super().save(*args, **kwargs)