# seed.py

import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
django.setup()

from api.models import (
    Comment, Client, LeadStatus, Lead, User,
    Civilite, VisaType, TypeDemande,
    SituationFamiliale, SituationProfessionnelle
)

fake = Faker('fr_FR')

# 🧹 Supprimer les anciennes données
Comment.objects.all().delete()
Client.objects.all().delete()
Lead.objects.all().delete()
User.objects.exclude(email="admin@example.com").delete()
print("🗑️ Anciennes données supprimées")

# 👤 Créer les utilisateurs (1 admin, 1 par rôle)
roles_to_create = [
    User.Roles.ADMIN,
    User.Roles.ACCUEIL,
    User.Roles.JURISTE,
    User.Roles.CONSEILLER,
    User.Roles.COMPTABILITE,
]
role_users = {}

for role in roles_to_create:
    email = f"{role.lower()}@example.com"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": role.capitalize(),
            "last_name": "Demo",
            "role": role,
            "is_active": True,
            "is_staff": role == User.Roles.ADMIN,
            "is_superuser": role == User.Roles.ADMIN,
        }
    )
    user.set_password("Password@1")
    user.save()
    role_users[role] = user

# Admin principal
admin, _ = User.objects.get_or_create(
    email="admin@example.com",
    defaults={
        "first_name": "Admin",
        "last_name": "Super",
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
        "role": User.Roles.ADMIN,
    }
)
admin.set_password("Password@1")
admin.save()
role_users["ADMIN_MAIN"] = admin

print("✅ Utilisateurs pour chaque rôle créés :")
for role, user in role_users.items():
    print(f" - {user.email} (role: {user.role}, staff: {user.is_staff}, superuser: {user.is_superuser})")

# 📊 Statuts disponibles
all_statuses = [status[0] for status in LeadStatus.choices]

# ➕ Création de 1000 leads
leads_to_create = []
for i in range(1000):
    status = random.choice(all_statuses)
    assigned_user = random.choice(list(role_users.values()))
    # Certains statuts "RDV" → date de rdv, d'autres non
    if "RDV" in status:
        appointment_date = timezone.now() + timedelta(days=random.randint(-10, 15))
    else:
        appointment_date = None

    leads_to_create.append(
        Lead(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            appointment_date=appointment_date,
            created_at=timezone.now() - timedelta(days=random.randint(0, 45)),
            status=status,
            assigned_to=assigned_user
        )
    )
Lead.objects.bulk_create(leads_to_create)
print("✅ 1000 leads créés")

# 🗨️ Ajouter des commentaires pour chaque lead (0 à 4 par lead)
leads = Lead.objects.all()
comments_to_create = []
for lead in leads:
    for _ in range(random.randint(0, 4)):
        comments_to_create.append(Comment(
            lead=lead,
            author=random.choice(list(role_users.values())),
            content=fake.paragraph(nb_sentences=random.randint(1, 4)),
            created_at=timezone.now() - timedelta(days=random.randint(0, 14)),
            updated_at=timezone.now()
        ))
Comment.objects.bulk_create(comments_to_create)
print(f"✅ {len(comments_to_create)} commentaires ajoutés")

# 👤 Créer les données clients (1 par lead)
client_data_to_create = []
type_demande_vals = list(TypeDemande)
visa_types = list(VisaType)
civilites = list(Civilite)
sit_fam = list(SituationFamiliale)
sit_pro = list(SituationProfessionnelle)

for lead in leads:
    a_un_visa = random.choice([True, False])
    type_visa = random.choice(visa_types) if a_un_visa else None
    demande_formulee = random.choice([True, False])
    nb_enfants = random.randint(0, 5)
    nb_enfants_fr = random.randint(0, nb_enfants) if nb_enfants else 0

    # Types de demande : de 1 à tous, pour couvrir tous les cas
    nb_types_demande = random.randint(1, len(type_demande_vals))
    types_demande = random.sample(type_demande_vals, nb_types_demande)

    client_data_to_create.append(Client(
        lead=lead,
        civilite=random.choice(civilites),
        date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=65),
        lieu_naissance=fake.city(),
        pays=fake.country(),
        nationalite=fake.current_country(),
        adresse=fake.street_address(),
        code_postal=fake.postcode(),
        ville=fake.city(),
        date_entree_france=timezone.now().date() - timedelta(days=random.randint(365, 365 * 30)),
        a_un_visa=a_un_visa,
        type_visa=type_visa,
        statut_refugie_ou_protection=random.choice([True, False]),
        types_demande=types_demande,
        demande_deja_formulee=demande_formulee,
        demande_formulee_precise=fake.sentence(nb_words=random.randint(3, 12)) if demande_formulee else "",
        situation_familiale=random.choice(sit_fam),
        a_des_enfants=nb_enfants > 0,
        nombre_enfants=nb_enfants,
        nombre_enfants_francais=nb_enfants_fr,
        enfants_scolarises=random.choice([True, False]) if nb_enfants > 0 else False,
        naissance_enfants_details=fake.text(max_nb_chars=100) if nb_enfants else "",
        situation_pro=random.choice(sit_pro),
        domaine_activite=fake.job(),
        nombre_fiches_paie=random.randint(0, 6),
        date_depuis_sans_emploi=timezone.now().date() - timedelta(days=random.randint(30, 2000)) if random.choice([True, False]) else None,
        a_deja_eu_oqtf=random.choice([True, False]),
        date_derniere_oqtf=timezone.now().date() - timedelta(days=random.randint(30, 2000)) if random.choice([True, False]) else None,
        demarche_en_cours_administration=random.choice([True, False]),
        remarques=fake.text(max_nb_chars=200),
    ))

Client.objects.bulk_create(client_data_to_create)
print(f"✅ {len(client_data_to_create)} données clients variées ajoutées")