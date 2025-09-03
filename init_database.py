# ✅ scripts/setup_initial_data.py

import os

import boto3
import django
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

from api.leads.constants import ABSENT, PRESENT, RDV_CONFIRME, RDV_PLANIFIE

# 1. Chargement des variables d’environnement
load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings.dev")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

from api.leads.models import LeadStatus
from api.users.roles import UserRoles

# 2. Afficher la base de données utilisée
print(
    "🔍 Connexion à la base de données :",
    settings.DATABASES["default"]["HOST"],
    settings.DATABASES["default"]["NAME"],
)

# 3. Création du superadmin
User = get_user_model()
ADMIN_EMAIL = "jennifer@tds.fr"
FIRST_NAME = "Jennifer"
LAST_NAME = "Koskas"
PASSWORD = "adminTDS123"

if not User.objects.filter(email=ADMIN_EMAIL).exists():
    print(f"👤 Création du superutilisateur : {ADMIN_EMAIL}")
    User.objects.create_superuser(
        email=ADMIN_EMAIL,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        password=PASSWORD,
        role=UserRoles.ADMIN,
    )
    print("✅ Superutilisateur créé avec succès.")
else:
    print("ℹ️ Le superutilisateur existe déjà.")

# 4. Création des statuts de leads
DEFAULT_STATUSES = {
    RDV_CONFIRME: {"label": "Rendez-vous confirmé", "color": "#2dd4bf"},
    RDV_PLANIFIE: {"label": "Rendez-vous planifié", "color": "#60a5fa"},
    ABSENT: {"label": "Absent", "color": "#f87171"},
    PRESENT: {"label": "Présent", "color": "#34d399"},
}

print("📦 Création des statuts de leads...")

for code, data in DEFAULT_STATUSES.items():
    status, created = LeadStatus.objects.get_or_create(
        code=code,
        defaults={
            "label": data["label"],
            "color": data["color"],
        },
    )
    if created:
        print(f"✅ Statut créé : {code} ({data['label']})")
    else:
        print(f"ℹ️ Statut déjà existant : {code}")

# 5. Test de connexion à Scaleway (S3-Compatible)
print("🔗 Test de connexion à Scaleway...")
try:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_S3_REGION_NAME", "fr-par"),
    )
    buckets = s3.list_buckets()
    print("✅ Connexion à Scaleway réussie. Buckets disponibles :")
    for b in buckets.get("Buckets", []):
        print("   -", b["Name"])
except (NoCredentialsError, ClientError) as e:
    print("❌ Erreur de connexion à Scaleway :", str(e))

print("🎉 Initialisation terminée.")
