import os

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator


import os

def document_upload_path(instance, filename):
    """
    Stocke les fichiers sous :
    leads/documents/{LASTNAME_FIRSTNAME}/{CATEGORY}/{original_filename}
    """
    lead = getattr(instance, 'lead', None)
    if not lead:
        # fallback : au cas où instance.lead n’est pas chargé (ex: instance.lead_id seulement)
        return f"leads/documents/lead_{instance.lead_id}/{filename}"

    category = (instance.category or "AUTRE").strip().upper()

    last_name = getattr(lead, "last_name", "UNKNOWN").strip().replace(" ", "_").upper()
    first_name = getattr(lead, "first_name", "UNKNOWN").strip().replace(" ", "_").upper()

    base_filename, file_extension = os.path.splitext(filename)
    safe_filename = base_filename.strip().replace(" ", "_")

    return f"{first_name}_{last_name}/{category}/{safe_filename}{file_extension}"

class Document(models.Model):
    class DocumentCategory(models.TextChoices):
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
    )

    category = models.CharField(
        max_length=50,
        choices=DocumentCategory.choices,
    )

    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name} - {self.get_category_display()}"