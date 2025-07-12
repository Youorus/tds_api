import io
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.users.models import User, UserRoles


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@user.com", first_name="Marc", last_name="Nkue", password="pwd", role=UserRoles.ADMIN
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestUserAvatarAPI:

    def test_post_method_not_allowed(self, api_client, user):
        url = reverse("user-avatar-detail", args=[user.id])
        resp = api_client.post(url)
        assert resp.status_code == 405
        # Pour DRF : "Méthode « POST » non autorisée."
        assert "non autorisée" in str(resp.data["detail"])

    def test_patch_avatar_success(self, api_client, user, mocker, settings):
        url = reverse("user-avatar-detail", args=[user.id])

        # Simuler MinioAvatarStorage.save() et settings
        mock_storage = mocker.patch("api.profile.views.MinioAvatarStorage")
        storage_instance = mock_storage.return_value
        storage_instance.save.return_value = "marc_nkue/avatar.jpg"
        settings.AWS_S3_ENDPOINT_URL = "https://cloud.test"
        settings.STORAGE_BACKEND = "minio"
        storage_instance.bucket_name = "avatars"
        storage_instance.location = ""

        file_content = io.BytesIO(b"avatar-image")
        file_content.name = "avatar.jpg"
        resp = api_client.patch(url, {"avatar": file_content}, format="multipart")
        assert resp.status_code == 200
        assert resp.data["avatar"].startswith("https://cloud.test/avatars/")

    def test_patch_avatar_no_file(self, api_client, user):
        url = reverse("user-avatar-detail", args=[user.id])
        resp = api_client.patch(url, {}, format="multipart")
        assert resp.status_code == 400
        assert "Aucun fichier reçu" in resp.data["detail"]

    def test_delete_avatar_success(self, api_client, user, mocker):
        url = reverse("user-avatar-detail", args=[user.id])
        user.avatar = "https://cloud.test/avatars/x.jpg"
        user.save()
        mocker.patch("api.profile.views.MinioAvatarStorage")
        resp = api_client.delete(url)
        assert resp.status_code == 204
        user.refresh_from_db()
        assert user.avatar is None

    def test_permission_required(self, db):
        # On ne s’authentifie PAS
        user = User.objects.create_user(
            email="test2@user.com", first_name="Paul", last_name="Martin", password="pwd", role=UserRoles.ADMIN
        )
        client = APIClient()
        url = reverse("user-avatar-detail", args=[user.id])
        resp = client.patch(url, {}, format="multipart")
        assert resp.status_code in (401, 403)
        resp = client.delete(url)
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestUserAvatarSerializer:
    def test_avatar_url_generation(self, user):
        from api.profile.serializers import UserAvatarSerializer
        user.avatar = "https://cloud.test/avatars/marc/avatar.jpg"
        serializer = UserAvatarSerializer(user, context={"request": None})
        data = serializer.data
        assert data["avatar"] == "https://cloud.test/avatars/marc/avatar.jpg"