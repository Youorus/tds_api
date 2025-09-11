import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from corsheaders.defaults import default_headers
from celery.schedules import crontab

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "changeme")
DEBUG = False
ALLOWED_HOSTS = []

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
    "rest_framework",
    "rest_framework_simplejwt",

    # Modules métier
    "api.custom_auth",
    "api.clients",
    "api.comments",
    "api.contracts",
    "api.documents",
    "api.lead_status",
    "api.leads",
    "api.payments",
    "api.profile",
    "api.services",
    "api.statut_dossier",
    "api.users",
    "api.booking",
    "api.appointment",
    "api.jurist_appointment",
    "api.websocket",
    "api.special_closing_period",
    "api.opening_hours",
    "api.jurist_availability_date",
    "api.user_unavailability",
]

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

TEMPLATES = [{
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
}]

# REST / JWT
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
    "REFRESH_COOKIE": "refresh_token",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True,
}

# Langue / Temps
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True
APPEND_SLASH = True

# PDF
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", "/usr/local/bin/wkhtmltopdf")

# Email
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.getenv("SERVER_EMAIL")

# Buckets
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

# Celery
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_BEAT_SCHEDULE = {
    "send-lead-reminders": {
        "task": "api.leads.tasks.send_reminder_emails",
        "schedule": crontab(minute=0, hour="*/1"),
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

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.tds-dossier.fr")