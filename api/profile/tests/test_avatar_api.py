import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import User

@pytest.mark.django_db
def test_avatar_upload_and_delete(tmp_path, django_user_model):
    # Création user
    user = django_user_model.objects.create_user(email="foo@bar.com", password="123", first_name="Foo", last_name="Bar")
    client = APIClient()
    client.force_authenticate(user=user)

    # PATCH upload avatar
    url = reverse("user-avatar-detail", args=[user.id])
    image_bytes = io.BytesIO(b"dummyimagecontent")
    image_bytes.name = "avatar.png"

    response = client.patch(url, {"avatar": image_bytes}, format="multipart")
    assert response.status_code == 200
    assert response.data["avatar"]

    # DELETE avatar
    response = client.delete(url)
    assert response.status_code == 204
    user.refresh_from_db()
    assert not user.avatar