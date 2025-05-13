# api/views/lead_document_viewset.py

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from botocore.exceptions import ClientError

from api.models import Document, Lead
from api.serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les documents liés à un lead :
    - POST : upload de 1+ fichiers
    - GET : liste ou filtrage par ?lead_id=
    - GET /{id} : un document
    - PATCH : modifier catégorie
    - DELETE : supprime le fichier du bucket et le document
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Document.objects.all()

    def get_queryset(self):
        """
        Permet de filtrer les documents par lead_id (?lead_id=123).
        """
        lead_id = self.request.query_params.get('lead_id')
        queryset = super().get_queryset()
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        return queryset.order_by("id")

    def perform_create(self, serializer):
        """
        Sauvegarde un ou plusieurs documents en utilisant le backend de stockage défini.
        """
        try:
            instances = serializer.save()
            if not isinstance(instances, list):
                instances = [instances]

            # (facultatif) Affiche en console le backend utilisé
            for instance in instances:
                print(f"✅ Stocké avec : {instance.file.storage.__class__.__name__}")
        except ClientError as e:
            raise serializers.ValidationError(
                {"detail": "Échec de l'upload vers le stockage distant."}
            )

    def create(self, request, *args, **kwargs):
        """
        Upload d’un ou plusieurs fichiers avec les champs :
        - lead : ID du lead
        - category : catégorie de document
        - file : un ou plusieurs fichiers
        """
        files = request.FILES.getlist('file')
        lead_id = request.data.get('lead')
        category = request.data.get('category')

        if not lead_id or not category:
            return Response(
                {"detail": "Champs 'lead' et 'category' requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        get_object_or_404(Lead, pk=lead_id)

        if not files:
            return Response(
                {"detail": "Aucun fichier reçu."},
                status=status.HTTP_400_BAD_REQUEST
            )

        document_data = [
            {"lead": lead_id, "category": category, "file": file}
            for file in files
        ]

        serializer = self.get_serializer(
            data=document_data,
            many=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({
            "message": f"{len(files)} document(s) uploadé(s) avec succès.",
            "documents": serializer.data
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime le document et son fichier distant (bucket S3 / MinIO).
        """
        instance = self.get_object()
        try:
            if instance.file and instance.file.name:
                instance.file.delete(save=False)
        except Exception:
            pass  # on ignore l’erreur si le fichier n’existe plus
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)