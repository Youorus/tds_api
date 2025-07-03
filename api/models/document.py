from django.db import models

class Document(models.Model):
    """
    Stocke un document lié à un client, avec un fichier dans le cloud (S3/MinIO/autre).
    - RGPD friendly : aucune métadonnée superflue, juste ce qui est utile métier.
    """
    client = models.ForeignKey(
        "Client",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Client associé"
    )
    url = models.URLField(
        verbose_name="URL du document"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d’envoi"
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        # Affichage lisible dans l’admin
        return f"{self.client} — {self.url.split('/')[-1]}"