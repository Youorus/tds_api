from .base import *
import os

# ─── ENV DEV ─────────────────────────────────────────────────
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Base de données SQLite (dev locale)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Fichiers statiques
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# CORS / CSRF en local
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]

# MinIO local (non sécurisé)
AWS_S3_ENDPOINT_URL = "http://localhost:9000"
AWS_ACCESS_KEY_ID = "minioadmin"
AWS_SECRET_ACCESS_KEY = "minioadmin123"
AWS_S3_VERIFY = False

# Sécurité locale (pas de HTTPS)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery local avec Redis non-SSL
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BROKER_TRANSPORT_OPTIONS = {}

# Channels local
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}
