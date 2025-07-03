from storages.backends.s3boto3 import S3Boto3Storage


class MinioMediaStorage(S3Boto3Storage):
    """
    Stockage générique pour les documents divers.
    Chemin : documents/
    """
    bucket_name = 'lead-documents'
    location = 'documents'
    file_overwrite = False


class MinioAvatarStorage(S3Boto3Storage):
    """
    Backend dédié pour les avatars utilisateurs.
    """
    bucket_name = 'avatars'
    location = ''
    file_overwrite = False


class MinioReceiptStorage(S3Boto3Storage):
    """
    Backend dédié pour les reçus de paiement PDF.
    Chemin : receipts/<receipt_id>_<client_name>.pdf
    """
    bucket_name = 'recus'
    location = ''
    file_overwrite = False


class MinioContractStorage(S3Boto3Storage):
    """
    Backend dédié pour les reçus de paiement PDF.
    Chemin : receipts/<receipt_id>_<client_name>.pdf
    """
    bucket_name = 'contracts'
    location = ''
    file_overwrite = False


class MinioDocumentStorage(S3Boto3Storage):
    """
    Backend dédié pour les reçus de paiement PDF.
    Chemin : receipts/<receipt_id>_<client_name>.pdf
    """
    bucket_name = 'documents-clients'
    location = ''
    file_overwrite = False