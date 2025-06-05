import os
import django
import random
from random import choice
from datetime import timedelta
from django.utils import timezone
from faker import Faker
import phonenumbers
from phonenumbers import PhoneNumberFormat
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
django.setup()

from api.models import (
    Comment, Client, Lead, LeadStatus, StatutDossier, User,
    Civilite, VisaType, SituationFamiliale,
    SituationProfessionnelle, SourceInformation, PaymentReceipt
)
from api.models.payment import Payment, PaymentMode, SERVICE_PRICES, ServiceTarifaire

fake = Faker("fr_FR")

DEMANDES_POSSIBLES = [
    "TITRE_SEJOUR",
    "RENOUVELLEMENT",
    "NATURALISATION",
    "DEMANDE_VISA",
    "REGROUPEMENT_FAMILIAL",
    "SUIVI_NATURALISATION",
    "DUPLICATA",
    "SUIVI_DOSSIER",
    "DCEM",
    "PRISE_RDV",
    "AUTRES",
]

def generate_french_phone_number():
    prefix = random.choice(["06", "07"])
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    number = prefix + suffix
    phone_obj = phonenumbers.parse(number, "FR")
    return phonenumbers.format_number(phone_obj, PhoneNumberFormat.E164)

# Nettoyage
print("\U0001f9f9 Suppression des données existantes...")
Comment.objects.all().delete()
PaymentReceipt.objects.all().delete()
Payment.objects.all().delete()
Client.objects.all().delete()
Lead.objects.all().delete()
User.objects.exclude(email="admin@example.com").delete()

# Utilisateurs
print("\U0001f465 Création des utilisateurs...")
users_info = [
    ("admin@example.com", "Admin", "User", User.Roles.ADMIN),
    ("mtakoumba@gmail.com", "Admin", "User", User.Roles.ADMIN),
    ("accueil@example.com", "Accueil", "User", User.Roles.ACCUEIL),
    ("conseiller1@example.com", "Conseiller1", "User", User.Roles.CONSEILLER),
    ("conseiller2@example.com", "Conseiller2", "User", User.Roles.CONSEILLER),
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
    print(f" ✅ {email} ({role})")

conseillers = [u for u in user_map.values() if u.role == User.Roles.CONSEILLER]

# Leads
print("📞 Génération de leads...")
leads = []
for _ in range(1):
    status = random.choice([s[0] for s in LeadStatus.choices])
    lead = Lead(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        phone=generate_french_phone_number(),
        appointment_date=timezone.now() + timedelta(days=random.randint(-5, 20)) if "RDV" in status else None,
        status=status,
        statut_dossier=random.choice([s[0] for s in StatutDossier.choices]),
        assigned_to=random.choice(conseillers),
    )
    lead.save()
    leads.append(lead)
print(f"✅ {len(leads)} leads créés")

# Clients
print("🗂 Création des données client...")
clients = []
for lead in leads:
    nb_enfants = random.randint(0, 4)
    client = Client(
        lead=lead,
        source=random.sample([s[0] for s in SourceInformation.choices], k=2),
        civilite=random.choice([c[0] for c in Civilite.choices]),
        date_naissance=fake.date_of_birth(minimum_age=20, maximum_age=60),
        lieu_naissance=fake.city(),
        pays=fake.country(),
        nationalite=fake.current_country(),
        adresse=fake.street_address(),
        code_postal=fake.postcode(),
        ville=fake.city(),
        date_entree_france=timezone.now().date() - timedelta(days=random.randint(400, 4000)),
        a_un_visa=random.choice([True, False]),
        type_visa=random.choice([v[0] for v in VisaType.choices]),
        statut_refugie_ou_protection=random.choice([True, False]),
        type_demande=random.choice(DEMANDES_POSSIBLES),
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
    client.save()
    clients.append(client)
print(f"✅ {len(clients)} clients créés")

# Paiements
print("💳 Création des paiements...")
for client in clients:
    try:
        service = random.choice(list(ServiceTarifaire.values))
        base_price = SERVICE_PRICES[service]
        remise = random.choice([0, 10, 20])
        discount = Decimal(remise) / Decimal(100)
        real_amount_due = (base_price * (1 - discount)).quantize(Decimal("0.01"))

        total_receipts = random.choice([1, 2, 3])
        receipt_amount = (real_amount_due / total_receipts).quantize(Decimal("0.01"))

        plan = Payment.objects.create(
            client=client,
            created_by=random.choice(conseillers),
            service=service,
            amount_due=base_price,
            discount_percent=Decimal(remise),
        )

        today = timezone.now().date()
        total_paid = Decimal("0.00")

        for i in range(total_receipts):
            remaining = (real_amount_due - total_paid).quantize(Decimal("0.01"))
            is_last = i == total_receipts - 1
            actual_amount = remaining if is_last else min(receipt_amount, remaining)

            if actual_amount <= Decimal("0.00"):
                print(f"⚠️ Paiement ignoré (montant nul ou négatif) pour client {client.id}")
                break

            mode = random.choice([m[0] for m in PaymentMode.choices])
            next_due = (today + timedelta(days=30 * (i + 1))) if not is_last else None

            receipt = plan.pay(
                amount=actual_amount,
                mode=mode,
                user=random.choice(conseillers),
                next_due_date=next_due,
            )

            print(f"✅ Paiement {i+1}/{total_receipts} pour client {client.id}: {actual_amount} € ({mode})")
            total_paid += actual_amount

    except Exception as e:
        print(f"❌ Erreur pour client {client.id}: {e}")

print("✅ Paiements et reçus générés")

# Commentaires
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