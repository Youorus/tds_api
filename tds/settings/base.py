import os
from datetime import timedelta
from pathlib import Path

from redis import SSLConnection
from dotenv import load_dotenv
from corsheaders.defaults import default_headers
from celery.schedules import crontab

# ─── Chargement des variables d’environnement ───────────────
load_dotenv()

# ─── Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Django Core ────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "changeme")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# ─── Applications installées ────────────────────────────────
INSTALLED_APPS = [
    "corsheaders",
    "storages",
    "channels",
    "django_celery_beat",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "background_task",

    # API & Auth
    "rest_framework",
    "rest_framework_simplejwt",

    # Modules métier
    "api.custom_auth.apps.CustomAuthConfig",
    "api.clients.apps.ClientsConfig",
    "api.comments.apps.CommentsConfig",
    "api.contracts.apps.ContractsConfig",
    "api.documents.apps.DocumentsConfig",
    "api.lead_status.apps.LeadStatusConfig",
    "api.leads.apps.LeadsConfig",
    "api.payments.apps.PaymentsConfig",
    "api.profile.apps.ProfileConfig",
    "api.services.apps.ServicesConfig",
    "api.statut_dossier.apps.StatutDossierConfig",
    "api.users.apps.UsersConfig",
    "api.booking.apps.BookingConfig",
    "api.appointment.apps.AppointmentConfig",
    "api.jurist_appointment.apps.JuristAppointmentConfig",
    "api.websocket.apps.WebsocketConfig",
    "api.special_closing_period.apps.SpecialClosingPeriodConfig",
    "api.opening_hours.apps.OpeningHoursConfig",
    "api.jurist_availability_date.apps.JuristAvailabilityDateConfig",
    "api.user_unavailability.apps.UserUnavailabilityConfig",
]

# ─── Middleware ─────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tds.urls"
ASGI_APPLICATION = "tds.asgi.application"
AUTH_USER_MODEL = "users.user"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Templates ──────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─── REST Framework & JWT ───────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.custom_auth.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "AUTH_COOKIE": "access_token",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─── Redis / Channels / Celery ──────────────────────────────
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

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
CELERY_BROKER_TRANSPORT_OPTIONS = (
    {"ssl_cert_reqs": None} if CELERY_BROKER_URL.startswith("rediss://") else {}
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_BEAT_SCHEDULE = {
    "send-lead-reminders": {
        "task": "api.leads.tasks.send_reminder_emails",
        "schedule": crontab(minute="0", hour="*/1"),
    },
    "mark-leads-as-absent": {
        "task": "api.leads.tasks.mark_absent_leads",
        "schedule": crontab(minute="*/30"),
    },
    "send-payment-due-reminders": {
        "task": "api.payments.tasks.send_payment_due_reminders",
        "schedule": crontab(hour=7, minute=0),
    },
}

# ─── CORS / CSRF ─────────────────────────────────────────────
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost").split(",")
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization", "content-type"]

# ─── Sécurité ────────────────────────────────────────────────
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() in ("true", "1", "yes")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── Email SMTP ─────────────────────────────────────────────
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.getenv("SERVER_EMAIL")

# ─── Time & Langue ───────────────────────────────────────────
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

APPEND_SLASH = True

# ─── Génération de PDF ──────────────────────────────────────
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", "/usr/local/bin/wkhtmltopdf")

# ─── Stockage S3 (Scaleway / MinIO) ─────────────────────────
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "minio")
AWS_S3_VERIFY = os.getenv("AWS_S3_VERIFY", "True").lower() in ("true", "1", "yes")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://localhost:9000")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "fr-par")
AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")
AWS_QUERYSTRING_AUTH = False

# Buckets séparés
BUCKET_USERS_AVATARS = os.getenv("BUCKET_USERS_AVATARS", "avatars-tds")
BUCKET_CLIENT_DOCUMENTS = os.getenv("BUCKET_CLIENT_DOCUMENTS", "documents-clients")
BUCKET_CONTRACTS = os.getenv("BUCKET_CONTRACTS", "contracts")
BUCKET_RECEIPTS = os.getenv("BUCKET_RECEIPTS", "recus")

SCW_BUCKETS = {
    "avatars": BUCKET_USERS_AVATARS,
    "documents": BUCKET_CLIENT_DOCUMENTS,
    "contracts": BUCKET_CONTRACTS,
    "receipts": BUCKET_RECEIPTS,
}

# ─── Logging ─────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}