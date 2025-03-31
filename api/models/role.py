from django.db import models
from django.utils.translation import gettext_lazy as _
from .user import User

class Role(models.Model):
    """
    Modèle définissant les rôles fonctionnels des utilisateurs dans le système.
    Les utilisateurs avec le rôle ADMIN sont automatiquement promus super-utilisateurs.
    """

    class RoleType(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrateur')
        CONSEILLER = 'CONSEILLER', _('Conseiller')
        COMMERCIAL = 'COMMERCIAL', _('Commercial')
        CLIENT = 'CLIENT', _('Client')
        ACCUEIL = 'ACCUEIL', _('Agent d\'accueil')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='role',
        verbose_name=_('utilisateur associé'),
        help_text=_('Utilisateur auquel ce rôle est attribué')
    )

    role_type = models.CharField(
        _('type de rôle'),
        max_length=20,
        choices=RoleType.choices,
        help_text=_('Rôle fonctionnel attribué à l\'utilisateur')
    )

    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True,
        help_text=_('Date et heure de création de ce rôle')
    )

    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True,
        help_text=_('Date et heure de dernière modification de ce rôle')
    )

    class Meta:
        verbose_name = _('rôle')
        verbose_name_plural = _('rôles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role_type'], name='role_type_idx'),
        ]

    def __str__(self):
        """Représentation textuelle du rôle (email + type de rôle)"""
        return f"{self.user.email} - {self.get_role_type_display()}"

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour :
        - Promouvoir automatiquement les ADMIN en super-utilisateurs
        - Révoquer les droits super-utilisateur si le rôle change
        """
        if self.role_type == self.RoleType.ADMIN:
            self.user.is_staff = True
            self.user.is_superuser = True
        else:
            # On conserve is_staff pour permettre l'accès à l'admin
            # mais on retire les droits super-utilisateur
            self.user.is_superuser = False

        self.user.save()
        super().save(*args, **kwargs)