import os

from api.users.roles import UserRoles

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
import django
django.setup()

import random
from decimal import Decimal
from datetime import timedelta
from faker import Faker
from django.utils import timezone
import phonenumbers
from phonenumbers import PhoneNumberFormat

# Import depuis chaque module
from api.comments.models import Comment
from api.contracts.models import Contract
from api.clients.models import Client
from api.leads.models import Lead
from api.users.models import User
from api.lead_status.models import LeadStatus
from api.statut_dossier.models import StatutDossier
from api.clients.enums import SourceInformation, Civilite, VisaType, SituationFamiliale, SituationProfessionnelle
from api.services.models import Service
from api.documents.models import Document
from api.payments.enums import PaymentMode
from api.payments.models import PaymentReceipt

fake = Faker("fr_FR")

def generate_french_phone_number():
    prefix = random.choice(["06", "07"])
    suffix = ''.join(str(random.randint(0, 9)) for _ in range(8))
    number = prefix + suffix
    phone_obj = phonenumbers.parse(number, "FR")
    return phonenumbers.format_number(phone_obj, PhoneNumberFormat.E164)

# --- Nettoyage
print("🧹 Suppression des données...")
Comment.objects.all().delete()
PaymentReceipt.objects.all().delete()
Contract.objects.all().delete()
Document.objects.all().delete()
Client.objects.all().delete()
Lead.objects.all().delete()
User.objects.exclude(email="admin@example.com").delete()
Service.objects.all().delete()
LeadStatus.objects.all().delete()
StatutDossier.objects.all().delete()

# --- SERVICES ---
SERVICES_SEED = [
    {"code": "TITRE_SEJOUR", "label": "Titre de séjour", "price": Decimal("1590.00")},
    {"code": "REGROUPEMENT_FAMILIAL", "label": "Regroupement familial", "price": Decimal("1590.00")},
    {"code": "NATURALISATION", "label": "Naturalisation", "price": Decimal("1290.00")},
    {"code": "RENOUVELLEMENT", "label": "Renouvellement", "price": Decimal("990.00")},
    {"code": "SUIVI_NATURALISATION", "label": "Suivi naturalisation", "price": Decimal("990.00")},
    {"code": "DEMANDE_VISA", "label": "Demande de visa", "price": Decimal("990.00")},
    {"code": "DUPLICATA", "label": "Duplicata", "price": Decimal("990.00")},
    {"code": "SUIVI_DOSSIER", "label": "Suivi de dossier", "price": Decimal("690.00")},
    {"code": "DCEM", "label": "DCEM", "price": Decimal("590.00")},
    {"code": "PRISE_RDV", "label": "Prise de RDV", "price": Decimal("0.00")},
    {"code": "AUTRES", "label": "Autres", "price": Decimal("0.00")},
]
service_map = {}
for s in SERVICES_SEED:
    service, _ = Service.objects.get_or_create(code=s["code"], defaults=s)
    service_map[s["code"]] = service

# --- STATUTS LEAD ---
LEAD_STATUSES = [
    {"code": "RDV_CONFIRME", "label": "Rendez-vous confirmé", "color": "#60a5fa"},
    {"code": "RDV_PLANIFIE", "label": "Rendez-vous planifié", "color": "#818cf8"},
    {"code": "PRESENT", "label": "Présent", "color": "#34d399"},
    {"code": "ABSENT", "label": "Absent", "color": "#f87171"},
]
lead_status_map = {}
for s in LEAD_STATUSES:
    status, _ = LeadStatus.objects.get_or_create(code=s["code"], defaults=s)
    lead_status_map[s["code"]] = status

# --- STATUTS DOSSIER ---
DOSSIER_STATUSES = [
    {"code": "EN_ATTENTE", "label": "En attente", "color": "#cccccc"},
    {"code": "INCOMPLET", "label": "Incomplet", "color": "#fbbf24"},
    {"code": "COMPLET", "label": "Complet", "color": "#34d399"},
    {"code": "VALIDE", "label": "Validé", "color": "#4ade80"},
    {"code": "REFUSE", "label": "Refusé", "color": "#f87171"},
]
dossier_status_map = {}
for s in DOSSIER_STATUSES:
    status, _ = StatutDossier.objects.get_or_create(code=s["code"], defaults=s)
    dossier_status_map[s["code"]] = status

# --- Utilisateurs ---
print("👤 Création des utilisateurs...")

users_info = [
    ("admin@example.com", "Admin", "User", UserRoles.ADMIN),
    ("mtakoumba@gmail.com", "Admin", "User", UserRoles.ADMIN),
    ("accueil@example.com", "Accueil", "User", UserRoles.ACCUEIL),
    ("conseiller1@example.com", "Conseiller1", "User", UserRoles.CONSEILLER),
    ("conseiller2@example.com", "Conseiller2", "User", UserRoles.CONSEILLER),
]
user_map = {}
for email, first, last, role in users_info:
    user, _ = User.objects.update_or_create(
        email=email,
        defaults={"first_name": first, "last_name": last, "role": role, "is_active": True}
    )
    user.set_password("Password@1")
    user.save()
    user_map[email] = user
    print(f"✅ {email} ({role})")
conseillers = [u for u in user_map.values() if u.role == UserRoles.CONSEILLER]

# --- Leads ---
print("📞 Création des leads...")
leads = []
for _ in range(10):
    status = random.choice(list(lead_status_map.values()))
    dossier_status = random.choice(list(dossier_status_map.values()))
    lead = Lead.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        phone=generate_french_phone_number(),
        appointment_date=timezone.now() + timedelta(days=random.randint(0, 15)) if "RDV" in status.code else None,
        status=status,
        statut_dossier=dossier_status,
        assigned_to=random.choice(conseillers),
    )
    leads.append(lead)
print(f"✅ {len(leads)} leads créés")

# --- Clients et Documents ---
print("📁 Création des clients et documents...")
clients = []
for lead in leads:
    nb_enfants = random.randint(0, 3)
    type_demande_code = random.choice(list(service_map.keys()))
    client = Client.objects.create(
        lead=lead,
        source=random.sample([s[0] for s in SourceInformation.choices], k=2),
        civilite=random.choice([c[0] for c in Civilite.choices]),
        date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=60),
        lieu_naissance=fake.city(),
        pays=fake.country(),
        nationalite=fake.current_country(),
        adresse=fake.street_address(),
        code_postal=fake.postcode(),
        ville=fake.city(),
        date_entree_france=timezone.now().date() - timedelta(days=random.randint(1000, 4000)),
        a_un_visa=random.choice([True, False]),
        type_visa=random.choice([v[0] for v in VisaType.choices]),
        statut_refugie_ou_protection=random.choice([True, False]),
        type_demande=service_map[type_demande_code],
        demande_deja_formulee=random.choice([True, False]),
        demande_formulee_precise=fake.sentence() if random.random() < 0.3 else "",
        situation_familiale=random.choice([s[0] for s in SituationFamiliale.choices]),
        a_des_enfants=nb_enfants > 0,
        nombre_enfants=nb_enfants,
        nombre_enfants_francais=random.randint(0, nb_enfants),
        enfants_scolarises=random.choice([True, False]) if nb_enfants else False,
        naissance_enfants_details=fake.text(100) if nb_enfants else "",
        situation_pro=random.choice([p[0] for p in SituationProfessionnelle.choices]),
        domaine_activite=fake.job(),
        nombre_fiches_paie=random.randint(1, 6),
        a_deja_eu_oqtf=random.choice([True, False]),
        remarques=fake.sentence(),
    )
    clients.append(client)

    doc_urls = [
        "https://www.africau.edu/images/default/sample.pdf",
        "https://file-examples.com/storage/fe73f36e226f5c4e8cb08a2/2017/10/file-example_PDF_1MB.pdf",
        "https://randomuser.me/api/portraits/men/32.jpg",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&h=800&auto=format",
    ]
    for url in random.sample(doc_urls, k=random.randint(1, 3)):
        Document.objects.create(client=client, url=url)
print(f"✅ {len(clients)} clients créés avec documents mock")

# --- Paiements & Contrats ---
print("💶 Génération des paiements...")
for client in clients:
    try:
        service = client.type_demande
        base_price = service.price
        remise = random.choice([0, 10, 20])
        discount = Decimal(remise)
        ratio = (Decimal("100") - discount) / Decimal("100")
        real_amount_due = (base_price * ratio).quantize(Decimal("0.01"))
        contract = Contract.objects.create(
            client=client,
            created_by=random.choice(conseillers),
            service=service,
            amount_due=base_price,
            discount_percent=discount,
        )
        total_receipts = random.choice([1, 2, 3])
        receipt_amount = (real_amount_due / total_receipts).quantize(Decimal("0.01"))
        total_paid = Decimal("0.00")
        today = timezone.now().date()
        for i in range(total_receipts):
            is_last = (i == total_receipts - 1)
            remaining = (real_amount_due - total_paid).quantize(Decimal("0.01"))
            actual_amount = remaining if is_last else min(receipt_amount, remaining)
            if actual_amount <= Decimal("0.00"):
                break
            next_due = (today + timedelta(days=30 * (i + 1))) if not is_last else None
            PaymentReceipt.objects.create(
                client=client,
                contract=contract,
                amount=actual_amount,
                mode=random.choice([m[0] for m in PaymentMode.choices]),
                payment_date=timezone.now(),
                created_by=random.choice(conseillers),
                next_due_date=next_due,
            )
            total_paid += actual_amount
        print(f"✅ Contrat {contract.id} créé avec {total_receipts} reçu(s) pour client {client.id}")
    except Exception as e:
        print(f"❌ Erreur pour client {client.id}: {e}")
print("✅ Paiements et reçus générés")

# --- Commentaires
print("💬 Création de commentaires...")
comments = []
for lead in leads:
    for _ in range(random.randint(0, 2)):
        comments.append(Comment(
            lead=lead,
            author=random.choice(conseillers),
            content=fake.paragraph(),
        ))
Comment.objects.bulk_create(comments)
print("✅ Commentaires ajoutés")