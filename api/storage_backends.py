# api/storage_backends.py
from storages.backends.s3boto3 import S3Boto3Storage

class MinioMediaStorage(S3Boto3Storage):
    bucket_name = 'lead-documents'
    location = 'documents'
    file_overwrite = False


class MinioAvatarStorage(S3Boto3Storage):
    """
    Backend dédié pour le stockage des avatars utilisateurs.
    Stocke dans: avatars/<user_id>/<uuid>.jpg
    """
    bucket_name = 'lead-documents'
    location = 'avatars'  # ✅ stocké dans: lead-documents/avatars/
    file_overwrite = False