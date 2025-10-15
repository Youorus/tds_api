import os
import django
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from unidecode import unidecode  # 🔥 pour supprimer accents

# --- Init Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings.prod")  # adapte si besoin
django.setup()

from api.leads.models import Lead
from api.lead_status.models import LeadStatus

# --- Config ---
FILE_PATH = "tds_venir.xlsx"
PARIS_TZ = ZoneInfo("Europe/Paris")

# --- Étape 1 : détecter la ligne d'en-tête ---
preview = pd.read_excel(FILE_PATH, header=None, nrows=20)
header_row = None
for i, row in preview.iterrows():
    if row.astype(str).str.contains("Nom", case=False, na=False).any():
        header_row = i
        break

if header_row is None:
    raise ValueError("❌ Impossible de trouver la ligne contenant 'Nom'")

# --- Étape 2 : lecture avec la bonne ligne en header ---
df = pd.read_excel(FILE_PATH, header=header_row)

# --- Étape 3 : normalisation colonnes ---
df.columns = [
    str(c).strip().lower()
    .replace(" ", "_")
    .replace("-", "_")
    .replace("é", "e")
    .replace("è", "e")
    .replace("ê", "e")
    .replace("à", "a")
    for c in df.columns
]

print("✅ Colonnes normalisées :", list(df.columns))

# --- Helper : trouver une colonne parmi plusieurs ---
def find_col(df, candidates):
    for c in df.columns:
        if c in candidates:
            return c
    raise KeyError(f"❌ Impossible de trouver une des colonnes : {candidates}")

# --- Colonnes clés ---
col_nom = find_col(df, ["nom"])
col_prenom = find_col(df, ["prenom"])
col_tel = find_col(df, ["telephone"])
col_email = find_col(df, ["e_mail", "email"])
col_conf = find_col(df, ["confirmation"])
col_statut_client = find_col(df, ["statut_client"])
col_date_rdv = find_col(df, ["date_de_rdv", "date_du_rdv"])
col_date_lead = find_col(df, ["date_du_lead", "lead_date"])

# --- Statut par défaut ---
try:
    default_status = LeadStatus.objects.get(code="RDV_PLANIFIE")
except LeadStatus.DoesNotExist:
    default_status = None

# --- Filtrer octobre ---
now = datetime.now(PARIS_TZ)
october_start = datetime(now.year, 10, 1, tzinfo=PARIS_TZ)
october_end = datetime(now.year, 10, 31, 23, 59, 59, tzinfo=PARIS_TZ)

# --- Dates ---
df[col_date_rdv] = pd.to_datetime(df[col_date_rdv], errors="coerce").dt.tz_localize(
    PARIS_TZ, nonexistent="NaT", ambiguous="NaT"
)
df[col_date_lead] = pd.to_datetime(df[col_date_lead], errors="coerce").dt.tz_localize(
    PARIS_TZ, nonexistent="NaT", ambiguous="NaT"
)

# --- Normalisation texte (supprime accents + minuscule) ---
df[col_statut_client] = (
    df[col_statut_client].astype(str).str.strip().apply(lambda x: unidecode(x).lower())
)
df[col_conf] = df[col_conf].astype(str).str.strip().apply(lambda x: unidecode(x).upper())

# --- Filtre ---
df_filtered = df[
    (df[col_statut_client].isin(["rdv valide", "rdv confirme"])) &
    (df[col_date_rdv].notna()) &
    (df[col_date_rdv].between(october_start, october_end))
]

print(f"📌 {len(df_filtered)} leads valides trouvés pour octobre")

# --- Préparation ---
leads_to_create = []
for _, row in df_filtered.iterrows():
    statut_client = row[col_statut_client]
    confirmation = row[col_conf]
    rdv_date = row[col_date_rdv]

    status = default_status

    if statut_client == "rdv confirme" and confirmation == "OK" and pd.notna(rdv_date):
        status = LeadStatus.objects.filter(code__iexact="RDV_CONFIRME").first()
    elif statut_client == "rdv valide" and pd.notna(rdv_date):
        status = LeadStatus.objects.filter(code__iexact="RDV_PLANIFIE").first()

    if not status:
        print(f"⚠️ Pas de statut trouvé pour: statut_client={row[col_statut_client]}, confirmation={row[col_conf]}")

    leads_to_create.append({
        "first_name": str(row.get(col_prenom, "")).capitalize(),
        "last_name": str(row.get(col_nom, "")).capitalize(),
        "email": row.get(col_email, None),
        "phone": str(row.get(col_tel, "")),
        "appointment_date": rdv_date,  # ✅ conserve date + heure + minute
        "created_at": row[col_date_lead] if pd.notna(row[col_date_lead]) else now,
        "status": status,
    })

# --- Aperçu ---
print("\n📌 Exemple des 5 premiers leads :")
for lead in leads_to_create[:5]:
    print(f"- {lead['first_name']} {lead['last_name']} | Statut={lead['status'].code if lead['status'] else '??'} | RDV={lead['appointment_date']}")

# --- Confirmation ---
confirm = input("\n👉 Voulez-vous insérer tous ces leads en base ? (o/n) : ")
if confirm.lower() == "o":
    for lead in leads_to_create:
        created_lead = Lead.objects.create(**lead)
        print(f"✅ Lead inséré : {created_lead.first_name} {created_lead.last_name} | Statut={created_lead.status.code if created_lead.status else '??'} | RDV={created_lead.appointment_date}")
    print(f"🎉 {len(leads_to_create)} leads insérés en base.")
else:
    print("❌ Insertion annulée.")