import uuid
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.utils.text import slugify

from api.profile.serializers import UserAvatarSerializer
from api.users.serializers import UserSerializer
from api.storage_backends import MinioAvatarStorage
from api.users.models import User


class UserAvatarViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour l’upload, la modification et la suppression des avatars utilisateur.
    PATCH = upload/update
    DELETE = suppression
    """
    serializer_class = UserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Utiliser PATCH pour mettre à jour l'avatar."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        file = request.FILES.get("avatar")
        if not file:
            print("[Avatar] Aucun fichier reçu.")
            return Response(
                {"detail": "Aucun fichier reçu."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        storage = MinioAvatarStorage()

        # Supprimer l'ancien avatar du bucket s'il existe
        if user.avatar:
            try:
                old_path = user.avatar.split(f"/{storage.bucket_name}/")[-1]
                print(f"[Avatar] Suppression ancien avatar : {old_path}")
                storage.delete(old_path)
            except Exception as e:
                print(f"[Avatar] Erreur suppression ancien avatar: {e}")

        # Génère le nom de fichier basé sur le nom de l'utilisateur
        first = slugify(user.first_name)
        last = slugify(user.last_name)
        ext = file.name.split(".")[-1].lower()  # Toujours .lower() pour éviter les bugs de case
        filename = f"{first}_{last}/{uuid.uuid4().hex}.{ext}"
        print(f"[Avatar] Nouveau nom de fichier : {filename}")

        # Sauvegarde dans MinIO
        saved_path = storage.save(filename, file)
        print(f"[Avatar] Fichier sauvegardé dans MinIO à : {saved_path}")

        # Construit l’URL publique propre
        if settings.STORAGE_BACKEND == "aws":
            avatar_url = (
                f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
                f"{storage.location}/{saved_path}"
            )
        else:
            location = f"{storage.location}/" if storage.location else ""
            avatar_url = (
                f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"
            )
        print(f"[Avatar] URL publique générée : {avatar_url}")

        # Mise à jour du modèle utilisateur
        user.avatar = avatar_url
        user.save()

        serializer = UserSerializer(user, context={"request": request})
        print(f"[Avatar] User mis à jour, réponse envoyée.")

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