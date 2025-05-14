import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker
import phonenumbers
from phonenumbers import PhoneNumberFormat

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
django.setup()

from api.models import (
    Comment, Client, LeadStatus, Lead, User,
    Civilite, VisaType, TypeDemande,
    SituationFamiliale, SituationProfessionnelle, StatutDossier, SourceInformation
)

fake = Faker('fr_FR')

# 📞 Génère un numéro de téléphone français valide (mobile uniquement)
def generate_french_phone_number():
    prefix = random.choice(["06", "07"])
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    number = prefix + suffix
    phone_obj = phonenumbers.parse(number, "FR")
    return phonenumbers.format_number(phone_obj, PhoneNumberFormat.E164)

# 🧹 Nettoyage
print("🧹 Suppression des anciennes données...")
Comment.objects.all().delete()
Client.objects.all().delete()
Lead.objects.all().delete()
User.objects.exclude(email="admin@example.com").delete()

# 👤 Utilisateurs
print("👤 Création des utilisateurs...")
users_info = [
    ("admin@example.com", "Admin", "User", User.Roles.ADMIN),
    ("accueil@example.com", "Accueil", "User", User.Roles.ACCUEIL),
    ("conseiller1@example.com", "Conseiller1", "User", User.Roles.CONSEILLER),
    ("conseiller2@example.com", "Conseiller2", "User", User.Roles.CONSEILLER),
]

user_map = {}
for email, first, last, role in users_info:
    user, _ = User.objects.update_or_create(
        email=email,
        defaults={
            "first_name": first,
            "last_name": last,
            "role": role,
            "is_active": True,
        }
    )
    user.set_password("Password@1")
    user.save()
    user_map[email] = user
    print(f" ✅ {email} (rôle : {role})")

conseillers = [u for u in user_map.values() if u.role == User.Roles.CONSEILLER]

# 📊 Statuts disponibles
lead_statuses = [s[0] for s in LeadStatus.choices]
statut_dossiers = [s[0] for s in StatutDossier.choices]

# ➕ Leads
print("📈 Création de 5000 leads...")
leads = []
for _ in range(5000):
    status = random.choice(lead_statuses)
    rdv = timezone.now() + timedelta(days=random.randint(-10, 30)) if "RDV" in status else None
    leads.append(Lead(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email() if random.random() < 0.8 else None,
        phone=generate_french_phone_number(),  # ✅ numéro FR valide
        appointment_date=rdv,
        status=status,
        statut_dossier=random.choice(statut_dossiers),
        created_at=timezone.now() - timedelta(days=random.randint(0, 60)),
        assigned_to=random.choice(conseillers),
    ))
Lead.objects.bulk_create(leads)

leads = Lead.objects.all()
print(f" ✅ {leads.count()} leads créés")

# 🗨️ Commentaires
print("💬 Ajout de commentaires...")
comments = []
for lead in leads:
    for _ in range(random.randint(0, 3)):
        comments.append(Comment(
            lead=lead,
            author=random.choice(conseillers),
            content=fake.paragraph(nb_sentences=random.randint(1, 3)),
            created_at=timezone.now() - timedelta(days=random.randint(0, 10)),
            updated_at=timezone.now(),
        ))
Comment.objects.bulk_create(comments)
print(f" ✅ {len(comments)} commentaires ajoutés")

# 🧾 Données client
print("📋 Création des données clients...")
clients = []
for lead in leads:
    a_un_visa = random.choice([True, False])
    demande_formulee = random.choice([True, False])
    nb_enfants = random.randint(0, 4)
    nb_enfants_fr = random.randint(0, nb_enfants)
    source = random.sample([s[0] for s in SourceInformation.choices], k=random.randint(1, 3))


    clients.append(Client(
        lead=lead,
        civilite=random.choice([c[0] for c in Civilite.choices]),
        source=source,
        date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=65),
        lieu_naissance=fake.city(),
        pays=fake.country(),
        nationalite=fake.current_country(),
        adresse=fake.street_address(),
        code_postal=fake.postcode(),
        ville=fake.city(),
        date_entree_france=timezone.now().date() - timedelta(days=random.randint(365, 365 * 20)),
        a_un_visa=a_un_visa,
        type_visa=random.choice([v[0] for v in VisaType.choices]) if a_un_visa else "",
        statut_refugie_ou_protection=random.choice([True, False]),
        types_demande=random.sample([t[0] for t in TypeDemande.choices], random.randint(1, 3)),
        demande_deja_formulee=demande_formulee,
        demande_formulee_precise=fake.sentence(nb_words=5) if demande_formulee else "",
        situation_familiale=random.choice([s[0] for s in SituationFamiliale.choices]),
        a_des_enfants=nb_enfants > 0,
        nombre_enfants=nb_enfants,
        nombre_enfants_francais=nb_enfants_fr,
        enfants_scolarises=random.choice([True, False]) if nb_enfants else False,
        naissance_enfants_details=fake.text(100) if nb_enfants else "",
        situation_pro=random.choice([p[0] for p in SituationProfessionnelle.choices]),
        domaine_activite=fake.job(),
        nombre_fiches_paie=random.randint(0, 6),
        date_depuis_sans_emploi=(timezone.now().date() - timedelta(days=random.randint(30, 2000))) if random.random() < 0.4 else None,
        a_deja_eu_oqtf=random.choice([True, False]),
        date_derniere_oqtf=(timezone.now().date() - timedelta(days=random.randint(30, 2000))) if random.random() < 0.3 else None,
        demarche_en_cours_administration=random.choice([True, False]),
        remarques=fake.text(200),
    ))
Client.objects.bulk_create(clients)
print(f" ✅ {len(clients)} clients créés")