
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.models import Comment
from api.serializers.comment_serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.all().select_related("author", "lead")

    @action(detail=False, methods=["get"], url_path="lead/(?P<lead_id>[^/.]+)")
    def by_lead(self, request, lead_id=None):
        """
        Retourne les commentaires d’un lead spécifique
        """
        queryset = self.get_queryset().filter(lead__id=lead_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        if not self._is_comment_author(serializer.instance):
            raise PermissionDenied(_("Vous n'êtes pas l'auteur de ce commentaire."))
        serializer.save()

    def perform_destroy(self, instance):
        if not self._is_comment_author(instance):
            raise PermissionDenied(_("Vous n'êtes pas l'auteur de ce commentaire."))
        instance.delete()

    def _is_comment_author(self, comment):
        return comment.author == self.request.user or self.request.user.is_superuser