from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .user import User
from .lead import Lead

class Comment(models.Model):
    """
    Modèle représentant un commentaire associé à un lead.
    """
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('lead associé'),
        help_text=_('Lead auquel ce commentaire est associé')
    )

    author = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('auteur'),
        help_text=_('Auteur du commentaire')
    )

    content = models.TextField(
        _('contenu'),
        help_text=_('Contenu du commentaire')
    )

    created_at = models.DateTimeField(
        _('date de création'),
        default=timezone.now,
        help_text=_('Date et heure de création du commentaire')
    )

    class Meta:
        verbose_name = _('commentaire')
        verbose_name_plural = _('commentaires')
        ordering = ['-created_at']

    def __str__(self):
        return f"Commentaire par {self.author} le {self.created_at.strftime('%Y-%m-%d %H:%M')}"