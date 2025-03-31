from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'lead', 'author', 'author_name', 'content', 'created_at']
        extra_kwargs = {
            'lead': {
                'error_messages': {
                    'null': _('Un commentaire doit être associé à un lead.'),
                    'required': _('Veuillez spécifier un lead.')
                }
            },
            'author': {
                'error_messages': {
                    'null': _('Veuillez spécifier un auteur valide.'),
                    'required': _('Veuillez spécifier un auteur.')
                }
            },
            'content': {
                'error_messages': {
                    'blank': _('Le contenu du commentaire ne peut pas être vide.'),
                    'required': _('Veuillez saisir un contenu pour le commentaire.')
                }
            }
        }

    def validate_content(self, value):
        """Validation personnalisée pour le contenu du commentaire."""
        value = value.strip()

        if not value:
            raise serializers.ValidationError(_('Le commentaire ne peut pas être vide.'))
        if len(value) < 3:
            raise serializers.ValidationError(_('Le commentaire doit contenir au moins 3 caractères.'))
        if len(value) > 2000:
            raise serializers.ValidationError(_('Le commentaire ne peut pas dépasser 2000 caractères.'))

        return value

    def validate(self, data):
        """
        Validation au niveau de l'objet complet.
        Tu peux ajouter ici des règles spécifiques de logique métier.
        """
        if 'lead' in data and 'author' in data and data['author'] == data['lead'].assigned_to:
            # Ex : empêcher les assignés de commenter leurs propres leads ?
            pass
        return data