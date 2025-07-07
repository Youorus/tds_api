import pytest
from api.clients.models import Client
from api.documents.models import Document

@pytest.mark.django_db
def test_document_str_representation():
    client = Client.objects.create(
        # … champs requis
        first_name="Jean", last_name="Test"
    )
    doc = Document.objects.create(client=client, url="https://cloud/doc1.pdf")
    assert str(doc).endswith("doc1.pdf")