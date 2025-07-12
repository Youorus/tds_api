import pytest
from api.documents.models import Document
from api.documents.serializers import DocumentSerializer
from api.clients.models import Client
from api.leads.models import Lead
from api.lead_status.models import LeadStatus

@pytest.mark.django_db
class TestDocumentSerializer:
    @pytest.fixture
    def client(self):
        status = LeadStatus.objects.create(code="NOUVEAU", label="Nouveau", color="#C1E8FF")
        lead = Lead.objects.create(first_name="Marc", last_name="Nkue", status=status)
        return Client.objects.create(lead=lead)

    def test_serializer_output(self, client):
        doc = Document.objects.create(client=client, url="https://cloud.test/doc.pdf")
        data = DocumentSerializer(doc).data
        assert data["client"] == client.id
        assert data["url"] == "https://cloud.test/doc.pdf"
        assert "uploaded_at" in data

    def test_serializer_readonly_fields(self, client):
        doc = Document.objects.create(client=client, url="https://cloud.test/doc.pdf")
        serializer = DocumentSerializer(doc)
        assert serializer.fields["id"].read_only
        assert serializer.fields["uploaded_at"].read_only
        assert serializer.fields["url"].read_only