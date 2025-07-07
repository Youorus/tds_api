from api.documents.models import Document
from api.documents.serializers import DocumentSerializer

def test_document_serializer_fields():
    doc = Document(id=1, client=1, url="https://cloud/doc.pdf")
    serializer = DocumentSerializer(doc)
    assert set(serializer.data.keys()) == {"id", "client", "url", "uploaded_at"}