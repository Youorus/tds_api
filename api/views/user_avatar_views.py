# api/views/user_avatar_viewset.py

import uuid
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.utils.text import slugify
from api.models import User
from api.serializers.user_avatar_serializer import UserAvatarSerializer
from api.storage_backends import MinioAvatarStorage


class UserAvatarViewSet(viewsets.ModelViewSet):
    serializer_class = UserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Utiliser PATCH pour mettre à jour l'avatar."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        file = request.FILES.get('avatar')
        if not file:
            return Response({"detail": "Aucun fichier reçu."},
                            status=status.HTTP_400_BAD_REQUEST)

        storage = MinioAvatarStorage()

        # 1️⃣ Supprimer l'ancien avatar du bucket s'il existe
        if user.avatar:
            try:
                old_path = user.avatar.split(f"/{storage.bucket_name}/")[-1]
                storage.delete(old_path)
            except Exception as e:
                print(f"Erreur suppression ancien avatar: {e}")

        # 2️⃣ Génère le nom de dossier/fichier basé sur le nom de l'utilisateur
        first = slugify(user.first_name)
        last = slugify(user.last_name)
        ext = file.name.split('.')[-1]
        filename = f"{first}_{last}/{uuid.uuid4().hex}.{ext}"

        # 3️⃣ Sauvegarde le nouveau fichier dans le bucket avatars
        saved_path = storage.save(filename, file)

        # 4️⃣ Construit l’URL publique propre
        if settings.STORAGE_BACKEND == "aws":
            avatar_url = f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{storage.location}/{saved_path}"
        else:
            # Si storage.location == '' (racine), on évite le double slash
            location = f"{storage.location}/" if storage.location else ""
            avatar_url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"
            print(avatar_url)

        # 5️⃣ Mise à jour du modèle utilisateur
        user.avatar = avatar_url
        user.save()

        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            try:
                storage = MinioAvatarStorage()
                path = user.avatar.split(f"/{storage.bucket_name}/")[-1]
                storage.delete(path)
            except Exception:
                pass
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)