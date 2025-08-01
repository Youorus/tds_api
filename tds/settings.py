from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv
from celery.schedules import crontab
from corsheaders.defaults import default_headers

# Charger .env
load_dotenv()

# ==================== BASE DIR ====================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== DJANGO CORE ====================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ['*']

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3001")


# ==================== INSTALLED APPS ====================
INSTALLED_APPS = [
    'corsheaders',
    'storages',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    "channels",
    'sslserver',

    # API
    'rest_framework',
    'rest_framework_simplejwt',

    # App principale
    # Modules métiers (réels, **basés sur ta capture**)
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
    "api.appointment",
    "api.jurist_appointment",
    "api.websocket",
    "api.special_closing_period",
    "api.opening_hours",
    "api.jurist_availability_date",
    "api.user_unavailability",

    # Ajoute l'app pour background tasks
    'background_task',
]

ASGI_APPLICATION = "tds.asgi.application"


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==================== URL & WSGI ====================
ROOT_URLCONF = 'tds.urls'
WSGI_APPLICATION = 'tds.wsgi.application'

# ==================== TEMPLATES ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==================== DATABASE ====================
#DATABASES = {
#   'default': {
#       'ENGINE': 'django.db.backends.postgresql',
#       'NAME': os.getenv('DB_NAME'),
#       'USER': os.getenv('DB_USER'),
#       'PASSWORD': os.getenv('DB_PASSWORD'),
#       'HOST': os.getenv('DB_HOST'),
#       'PORT': os.getenv('DB_PORT', '5432'),
#   }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==================== AUTH ====================
AUTH_USER_MODEL = 'users.user'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== REST FRAMEWORK ====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

WKHTMLTOPDF_PATH = "/usr/local/bin/wkhtmltopdf"

SIMPLE_JWT = {
    'AUTH_COOKIE': None,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==================== CORS ====================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://192.168.1.159:3001",
]
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = list(default_headers) + ['authorization', 'content-type']

# ==================== STATIC / MEDIA ====================
STATIC_URL = 'static/'

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True


# ==================== EMAIL ====================
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.getenv("SERVER_EMAIL")

# ==================== STORAGE (MinIO / AWS S3) ====================
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "minio")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
AWS_S3_ADDRESSING_STYLE = "path"
AWS_QUERYSTRING_AUTH = False

if STORAGE_BACKEND == "minio":
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://localhost:9000")
    AWS_S3_VERIFY = False
    DEFAULT_FILE_STORAGE = 'api.storage_backends.MinioMediaStorage'
elif STORAGE_BACKEND == "aws":
    AWS_S3_ENDPOINT_URL = None
    AWS_S3_VERIFY = True
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

MEDIA_URL = (
    f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"
    if STORAGE_BACKEND == "aws"
    else f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
)

# ==================== AUTRES ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

