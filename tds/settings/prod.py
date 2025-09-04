from .base import *
import dj_database_url
import os
from redis import SSLConnection

# ─── Django Core ────────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# ─── Base de données PostgreSQL (ex: Render) ────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# ─── Fichiers statiques (collectés dans /staticfiles) ───────────
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ─── CORS / CSRF autorisés depuis domaines frontend ─────────────
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# ─── Redirection HTTPS et cookies sécurisés ─────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ─── Stockage Scaleway S3 ───────────────────────────────────────
STORAGE_BACKEND = "aws"

AWS_S3_VERIFY = os.getenv("AWS_S3_VERIFY", "True").lower() in ("true", "1", "yes")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "fr-par")
AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")

# Buckets séparés
BUCKET_USERS_AVATARS = os.getenv("BUCKET_USERS_AVATARS", "avatars-tds")
BUCKET_CLIENT_DOCUMENTS = os.getenv("BUCKET_CLIENT_DOCUMENTS", "documents-clients")
BUCKET_CONTRACTS = os.getenv("BUCKET_CONTRACTS", "contracts")
BUCKET_RECEIPTS = os.getenv("BUCKET_RECEIPTS", "recus")

# ─── Redis (Upstash en rediss://) pour Channels et Celery ───────
USE_UPSTASH = "upstash.io" in os.getenv("REDIS_URL", "")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{
                "address": os.getenv("REDIS_URL"),
                **({"connection_class": SSLConnection} if USE_UPSTASH else {}),
            }],
        },
    },
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_TRANSPORT_OPTIONS = {"ssl_cert_reqs": None}
else:
    CELERY_BROKER_TRANSPORT_OPTIONS = {}

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"