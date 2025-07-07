# api/utils/cloud/storage.py

from django.core.files.base import ContentFile
from django.utils.text import slugify
from tds import settings

from api.storage_backends import (
    MinioReceiptStorage,
    MinioContractStorage,
    MinioDocumentStorage,
)

def store_receipt_pdf(receipt, pdf_bytes: bytes) -> str:
    """
    Stocke le PDF d'un reçu dans MinIO/S3 et retourne l’URL publique.
    :param receipt: instance PaymentReceipt
    :param pdf_bytes: bytes du PDF
    :return: URL publique du reçu PDF
    """
    # ⚠️ Import local pour éviter le circular import
    # from api.payments.models import PaymentReceipt  # PAS NÉCESSAIRE sauf type checking

    lead = receipt.client.lead
    client_id = receipt.client.id
    client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client_id}")
    date_str = receipt.payment_date.strftime("%Y%m%d")
    filename = f"{client_slug}/recu_{receipt.id}_{date_str}.pdf"

    file_content = ContentFile(pdf_bytes)
    storage = MinioReceiptStorage()
    saved_path = storage.save(filename, file_content)

    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = (
            f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
            f"{storage.location}/{saved_path}"
        )
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url


def store_contract_pdf(contract, pdf_bytes: bytes) -> str:
    """
    Stocke le PDF d’un contrat dans MinIO/S3 et retourne l’URL publique.
    :param contract: instance Contract
    :param pdf_bytes: bytes du PDF
    :return: URL publique du PDF du contrat
    """
    # ⚠️ Import local pour éviter le circular import (inutile si pas de type checking)
    # from api.contracts.models import Contract

    client = contract.client
    lead = client.lead
    client_id = client.id
    client_slug = slugify(f"{lead.last_name}_{lead.first_name}_{client_id}")
    date_str = contract.created_at.strftime("%Y%m%d")

    filename = f"{client_slug}/contrat_{contract.id}_{date_str}.pdf"

    file_content = ContentFile(pdf_bytes)
    storage = MinioContractStorage()
    saved_path = storage.save(filename, file_content)

    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = (
            f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
            f"{storage.location}/{saved_path}"
        )
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url


def store_client_document(client, file_content, original_filename) -> str:
    """
    Stocke un document client dans MinIO/S3, retourne l’URL publique.
    :param client: instance Client
    :param file_content: bytes ou ContentFile ou InMemoryUploadedFile
    :param original_filename: str, nom d'origine (ex: "CNI.pdf")
    :return: URL publique du document
    """
    client_slug = slugify(f"{client.lead.last_name}_{client.lead.first_name}_{client.id}")
    ext = original_filename.split(".")[-1] if "." in original_filename else "pdf"
    safe_filename = slugify(original_filename.rsplit('.', 1)[0])
    filename = f"{client_slug}/{safe_filename}.{ext}"

    storage = MinioDocumentStorage()
    if isinstance(file_content, bytes):
        file_content = ContentFile(file_content, name=filename)
    saved_path = storage.save(filename, file_content)

    if getattr(settings, "STORAGE_BACKEND", "") == "aws":
        url = (
            f"https://{storage.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
            f"{storage.location}/{saved_path}"
        )
    else:
        location = f"{storage.location}/" if storage.location else ""
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{storage.bucket_name}/{location}{saved_path}"

    return url