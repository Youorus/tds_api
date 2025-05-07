# api/views/lead_document_viewset.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from api.models import Document
from api.serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour les documents des leads :
    - POST pour uploader (1 ou plusieurs fichiers)
    - GET pour lister tous les documents ou filtrer par lead
    - GET {id} pour voir un document précis
    - PATCH pour éditer la catégorie
    - DELETE pour supprimer un document
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Pour accepter les fichiers
    queryset = Document.objects.all()

    def get_queryset(self):
        """
        Option de filtrage dynamique par lead_id (query param ?lead_id=xxx)
        """
        queryset = Document.objects.all()
        lead_id = self.request.query_params.get('lead_id')

        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)

        return queryset

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')
        lead_id = request.data.get('lead')
        category = request.data.get('category')

        if not lead_id or not category:
            return Response({"detail": "Champs 'lead' et 'category' requis."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not files:
            return Response({"detail": "Aucun fichier reçu."},
                            status=status.HTTP_400_BAD_REQUEST)

        documents = []
        for file in files:
            document = Document(lead_id=lead_id, category=category)
            document.file.save(file.name, file, save=True)  #  Upload réel dans MinIO
            documents.append(document)

        serializer = self.get_serializer(documents, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Permet de modifier partiellement un document, ex: changer sa catégorie.
        (PATCH /api/documents/{id}/)
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime le document ET son fichier du storage.
        """
        instance = self.get_object()

        # 🔥 Supprime aussi le fichier physique
        instance.file.delete(save=False)
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)