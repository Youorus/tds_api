# api/views/user_avatar_viewset.py

import uuid
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

from api.models import User
from api.serializers import UserAvatarSerializer
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

        # 📁 Génère le chemin avatars/<user_id>/<uuid>.ext
        ext = file.name.split('.')[-1]
        filename = f"{user.id}/{uuid.uuid4().hex}.{ext}"

        # 📦 Sauvegarde dans avatars/ avec le backend dédié
        storage = MinioAvatarStorage()
        saved_path = storage.save(filename, file)

        # 🌐 Construit l’URL publique propre
        if settings.STORAGE_BACKEND == "aws":
            avatar_url = f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{storage.location}/{saved_path}"
        else:
            avatar_url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{storage.location}/{saved_path}"

        # 💾 Stocke l’URL dans user.avatar
        user.avatar = avatar_url
        user.save()

        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            try:
                path = user.avatar.split(f"/{settings.AWS_STORAGE_BUCKET_NAME}/")[-1]
                MinioAvatarStorage().delete(path)
            except Exception:
                pass
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)