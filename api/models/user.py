import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User.
    Implémente les méthodes nécessaires à la création d'utilisateurs et super-utilisateurs.
    """

    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        """
        Crée et enregistre un utilisateur standard avec l'email et le mot de passe fournis.

        Args:
            email (str): Adresse email de l'utilisateur
            first_name (str): Prénom de l'utilisateur
            last_name (str): Nom de famille de l'utilisateur
            password (str): Mot de passe en clair (optionnel)
            extra_fields: Arguments supplémentaires pour le modèle User

        Returns:
            User: Instance du nouvel utilisateur créé

        Raises:
            ValueError: Si l'email n'est pas fourni
        """
        if not email:
            raise ValueError(_('L\'email doit être renseigné'))

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        """
        Crée un super-utilisateur avec tous les droits administratifs.

        Args:
            email (str): Adresse email de l'administrateur
            first_name (str): Prénom de l'administrateur
            last_name (str): Nom de famille de l'administrateur
            password (str): Mot de passe en clair (optionnel)
            extra_fields: Arguments supplémentaires pour le modèle User

        Returns:
            User: Instance du nouvel administrateur créé

        Raises:
            ValueError: Si is_staff ou is_superuser ne sont pas True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le super-utilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le super-utilisateur doit avoir is_superuser=True.'))

        return self.create_user(email, first_name, last_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé remplaçant le modèle User par défaut de Django.
    Utilise l'email comme identifiant principal et UUID comme clé primaire.

    Hérite de:
        AbstractBaseUser: Fournit le cœur de l'implémentation utilisateur
        PermissionsMixin: Ajoute le système de permissions Django
    """

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
    REQUIRED_FIELDS = ['first_name', 'last_name']

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