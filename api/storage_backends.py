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
    Chemin : avatars/<user_id>/<uuid>.jpg
    """
    bucket_name = 'lead-documents'
    location = 'avatars'
    file_overwrite = False


class MinioReceiptStorage(S3Boto3Storage):
    """
    Backend dédié pour les reçus de paiement PDF.
    Chemin : receipts/<receipt_id>_<client_name>.pdf
    """
    bucket_name = 'lead-documents'
    location = 'receipts'
    file_overwrite = True  # permet d’écraser un reçu si le paiement est mis à jour


class MinioContractStorage(S3Boto3Storage):
    """
    Backend dédié pour les reçus de paiement PDF.
    Chemin : receipts/<receipt_id>_<client_name>.pdf
    """
    bucket_name = 'lead-documents'
    location = 'contracts'
    file_overwrite = True  # permet d’écraser un reçu si le paiement est mis à jour