# api/views/user_avatar_viewset.py

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from api.models import User
from api.serializers import UserAvatarSerializer

class UserAvatarViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer l'avatar des utilisateurs :
    - Upload
    - Voir avatar
    - Supprimer avatar
    - Mettre à jour avatar
    """
    serializer_class = UserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Upload d'un avatar pour un utilisateur existant (via PATCH ou PUT en général)
        """
        return Response({"detail": "Utiliser PATCH pour mettre à jour l'avatar."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        """
        Mettre à jour (ou ajouter) l'avatar d'un utilisateur.
        """
        user = self.get_object()

        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({"detail": "Aucun fichier reçu."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.avatar = avatar_file
        user.save()

        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Supprimer l'avatar d'un utilisateur.
        """
        user = self.get_object()
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)