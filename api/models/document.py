# api/models/document.py

import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

# 📦 Détermine dynamiquement le backend de stockage à utiliser
def get_storage_backend():
    from api.storage_backends import MinioMediaStorage
    return MinioMediaStorage() if settings.STORAGE_BACKEND == "minio" else S3Boto3Storage()

# 📁 Fonction de path dynamique avec structure propre
def document_upload_path(instance, filename):
    """
    Chemin de sauvegarde :
    JEAN_DUPONT/CNI/NOM_FICHIER.pdf
    """
    lead = getattr(instance, 'lead', None)
    category = (instance.category or "AUTRES").strip().upper()

    def slugify(value):
        return str(value).strip().replace(" ", "_").upper()

    if lead:
        last_name = slugify(getattr(lead, "last_name", "UNKNOWN"))
        first_name = slugify(getattr(lead, "first_name", "UNKNOWN"))
        base_filename, extension = os.path.splitext(filename)
        safe_filename = slugify(base_filename)

        return f"{first_name}_{last_name}/{category}/{safe_filename}{extension}"

    # Fallback si lead n’est pas chargé
    return f"lead_{instance.lead_id}/{category}/{filename}"

class Document(models.Model):
    """
    Document rattaché à un lead — fichier uploadé (PDF/JPG/PNG).
    Stockage S3/MinIO configuré dynamiquement.
    """

    class DocumentCategory(models.TextChoices):
        # 📂 Catégories documentaires standardisées
        CNI = "CNI", _("Carte d'identité")
        PASSEPORT = "PASSEPORT", _("Passeport")
        ACTE_NAISSANCE = "ACTE_NAISSANCE", _("Acte de naissance")
        JUSTIFICATIF_DOMICILE = "JUSTIFICATIF_DOMICILE", _("Justificatif de domicile")
        FACTURE = "FACTURE", _("Facture")
        FORMULAIRE = "FORMULAIRE", _("Formulaire officiel")
        PHOTO_IDENTITE = "PHOTO_IDENTITE", _("Photo d'identité")
        ATTESTATION_HEBERGEMENT = "ATTESTATION_HEBERGEMENT", _("Attestation d'hébergement")
        ACTE_MARIAGE = "ACTE_MARIAGE", _("Acte de mariage")
        LIVRET_FAMILLE = "LIVRET_FAMILLE", _("Livret de famille")
        CERTIFICAT_SCOLARITE = "CERTIFICAT_SCOLARITE", _("Certificat de scolarité")
        CONTRAT_TRAVAIL = "CONTRAT_TRAVAIL", _("Contrat de travail")
        FICHE_PAIE = "FICHE_PAIE", _("Fiche de paie")
        ATTESTATION_POLE_EMPLOI = "ATTESTATION_POLE_EMPLOI", _("Attestation Pôle Emploi")
        JUSTIFICATIF_RESSOURCES = "JUSTIFICATIF_RESSOURCES", _("Justificatif de ressources")
        RELEVE_BANCAIRE = "RELEVE_BANCAIRE", _("Relevé bancaire")
        VISA = "VISA", _("Visa")
        PERMIS_SEJOUR = "PERMIS_SEJOUR", _("Titre ou Permis de séjour")
        CASIER_JUDICIAIRE = "CASIER_JUDICIAIRE", _("Casier judiciaire")
        AUTRES = "AUTRES", _("Autres")

    id = models.AutoField(primary_key=True)

    lead = models.ForeignKey(
        "Lead",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Lead associé"
    )

    category = models.CharField(
        max_length=50,
        choices=DocumentCategory.choices,
        verbose_name="Catégorie"
    )

    file = models.FileField(
        upload_to=document_upload_path,
        storage=get_storage_backend(),  # ✅ dynamique MinIO / S3
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
        verbose_name="Fichier"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name} – {self.get_category_display()}"