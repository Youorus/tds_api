from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from api.models import Document
from api.serializers.document_serializer import DocumentSerializer
from api.utils.store_cloud import store_client_document


class DocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD complet des documents client, y compris upload de plusieurs fichiers.
    """
    queryset = Document.objects.select_related("client").all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get("client")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Upload d’un ou plusieurs fichiers :
        - files[] pour upload multiple, file pour un seul
        - client doit être passé en paramètre POST ou URL
        """
        client_id = request.data.get("client") or request.query_params.get("client")
        if not client_id:
            return Response({"detail": "client ID requis"}, status=400)
        from api.models import Client
        try:
            client = Client.objects.get(pk=client_id)
        except Client.DoesNotExist:
            return Response({"detail": "Client inexistant"}, status=404)

        files = request.FILES.getlist("files") or [request.FILES.get("file")]
        files = [f for f in files if f]  # Nettoie None si "file" absent

        documents = []
        for file in files:
            url = store_client_document(client, file, file.name)
            document = Document.objects.create(client=client, url=url)
            documents.append(document)

        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime un document côté DB ET dans le storage cloud (MinIO/S3).
        """
        instance = self.get_object()
        file_url = instance.url

        if file_url:
            try:
                from api.storage_backends import MinioDocumentStorage
                storage = MinioDocumentStorage()
                bucket_name = storage.bucket_name

                # On extrait le chemin relatif du fichier à supprimer (après le nom du bucket)
                split_token = f"/{bucket_name}/"
                if split_token in file_url:
                    path = file_url.split(split_token, 1)[1]
                else:
                    # fallback : extrait tout après le dernier slash du bucket
                    path = file_url.split("/")[-2] + "/" + file_url.split("/")[-1]
                if path.startswith("/"):
                    path = path[1:]
                storage.delete(path)
            except Exception as e:
                print(f"Erreur suppression du document dans le storage : {e}")

        # 2. Supprimer en DB (super)
        return super().destroy(request, *args, **kwargs)