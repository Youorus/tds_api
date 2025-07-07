import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from api.clients.models import Client
from api.documents.models import Document

@pytest.mark.django_db
def test_upload_and_delete_document(tmp_path, django_user_model):
    user = django_user_model.objects.create_user(email="u@x.com", password="pw")
    client_obj = Client.objects.create(first_name="Marie", last_name="Doc")
    client = APIClient()
    client.force_authenticate(user=user)

    # Upload fichier
    url = reverse("document-list")
    data = {
        "client": client_obj.id,
        "file": io.BytesIO(b"abc"),
    }
    data["file"].name = "test.pdf"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 201
    doc_id = response.data[0]["id"]

    # Suppression du document
    del_url = reverse("document-detail", args=[doc_id])
    response = client.delete(del_url)
    assert response.status_code == 204
    assert not Document.objects.filter(pk=doc_id).exists()