# api/views/lead_document_download_view.py

import io
import zipfile
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.models import Document

class DocumentDownloadView(APIView):
    """
    View pour télécharger UN ou PLUSIEURS documents :
    - Si 1 seul ID ➔ renvoyer directement le fichier
    - Si plusieurs IDs ➔ créer un ZIP dynamique
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = request.query_params.get('ids')

        if not ids:
            return Response({"detail": "Paramètre 'ids' requis (ex: ?ids=1 ou ?ids=1,2,3)."},
                            status=status.HTTP_400_BAD_REQUEST)

        ids_list = [int(pk) for pk in ids.split(',') if pk.isdigit()]
        documents = Document.objects.filter(id__in=ids_list)

        if not documents.exists():
            return Response({"detail": "Aucun document trouvé."},
                            status=status.HTTP_404_NOT_FOUND)

        if len(documents) == 1:
            # 🔥 Télécharger 1 seul document directement
            document = documents.first()
            return FileResponse(
                document.file,
                as_attachment=True,
                filename=document.file.name.split("/")[-1]
            )

        # 🔥 Télécharger plusieurs fichiers dans un ZIP
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documents:
                if doc.file and hasattr(doc.file, 'path'):
                    with open(doc.file.path, 'rb') as f:
                        file_data = f.read()

                    # Exemple : CNI/nomdufichier.pdf
                    filename_in_zip = f"{doc.category}/{doc.file.name.split('/')[-1]}"
                    zip_file.writestr(filename_in_zip, file_data)

        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="documents_selectionnes.zip",
            content_type='application/zip'
        )