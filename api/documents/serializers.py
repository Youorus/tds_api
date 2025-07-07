from rest_framework import serializers
from api.documents.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer de document (lecture/écriture).
    """
    class Meta:
        model = Document
        fields = ["id", "client", "url", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at", "url"]