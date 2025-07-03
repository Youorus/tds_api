from django.core.files.base import ContentFile
from django.utils.text import slugify

from api.models import PaymentReceipt, Contract
from api.storage_backends import MinioReceiptStorage, MinioContractStorage, MinioDocumentStorage
from tds import settings


def store_receipt_pdf(receipt: PaymentReceipt, pdf_bytes: bytes) -> str:
    """
    Stocke le PDF dans MinIO/S3, retourne l’URL publique.
    """
    lead = receipt.client.lead
    client_id = receipt.client.id
    # Slug du client@
    client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client_id}")
    # Date de création du reçu, format YYYYMMDD
    date_str = receipt.payment_date.strftime("%Y%m%d")
    # Chemin complet
    filename = f"{client_slug}/recu_{receipt.id}_{date_str}.pdf"

    file_content = ContentFile(pdf_bytes)
    storage = MinioReceiptStorage()
    saved_path = storage.save(filename, file_content)

    # Construction de l’URL publique (compatible MinIO ou S3)
    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{storage.location}/{saved_path}"
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url

def store_contract_pdf(contract: Contract, pdf_bytes: bytes) -> str:
    """
    Stocke le PDF du contrat dans MinIO/S3 et retourne l’URL publique.
    """
    client = contract.client
    lead = client.lead
    client_id = client.id
    client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client_id}")
    date_str = contract.created_at.strftime("%Y%m%d")

    # Ex : dupont_jean_42/contrat_107_20240702.pdf
    filename = f"{client_slug}/contrat_{contract.id}_{date_str}.pdf"

    file_content = ContentFile(pdf_bytes)
    storage = MinioContractStorage()
    saved_path = storage.save(filename, file_content)

    # Construction de l’URL publique (compatible MinIO/S3)
    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{storage.location}/{saved_path}"
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url

def store_client_document(client, file_content, original_filename) -> str:
    """
    Stocke un fichier dans le bucket MinIO/S3, dossier par client.
    Retourne l’URL publique.
    - client: instance du modèle Client
    - file_content: bytes ou ContentFile ou InMemoryUploadedFile
    - original_filename: nom d'origine (ex: CNI.pdf)
    """
    # Construire le chemin du fichier: NOM_PRENOM_ID/nom_de_fichier.ext
    client_slug = slugify(f"{client.lead.last_name}_{client.lead.first_name}_{client.id}")
    ext = original_filename.split(".")[-1] if "." in original_filename else "pdf"
    safe_filename = slugify(original_filename.rsplit('.', 1)[0])
    filename = f"{client_slug}/{safe_filename}.{ext}"

    # Stockage
    storage = MinioDocumentStorage()
    if isinstance(file_content, bytes):
        file_content = ContentFile(file_content, name=filename)
    saved_path = storage.save(filename, file_content)

    # Générer l’URL publique
    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{storage.location}/{saved_path}"
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url