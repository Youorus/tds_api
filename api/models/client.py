from django.db import models
from django.utils.translation import gettext_lazy as _
from .user import User

class Client(models.Model):
    """
    Modèle complémentaire pour stocker des informations spécifiques aux clients.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name=_('compte utilisateur'),
        help_text=_('Compte utilisateur de base associé à ce client')
    )

    phone = models.CharField(
        _('téléphone'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Numéro de téléphone au format international')
    )

    address = models.TextField(
        _('adresse postale'),
        blank=True,
        null=True,
        help_text=_('Adresse complète avec code postal et ville')
    )

    class Meta:
        verbose_name = _('client')
        verbose_name_plural = _('clients')
        ordering = ['-user__date_joined']

    def __str__(self):
        """Représentation textuelle du client (nom complet + client)"""
        return f"Client {self.user.get_full_name()}"