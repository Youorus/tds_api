# seed.py

import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
django.setup()

from api.models import Comment, Client, LeadStatus, Lead, User, Civilite, VisaType, TypeDemande, SituationFamiliale, SituationProfessionnelle




fake = Faker('fr_FR')

# 🧹 Supprimer les anciennes données
Comment.objects.all().delete()
Client.objects.all().delete()
Lead.objects.all().delete()
print("🗑️ Anciennes données supprimées")

# 👤 Créer un utilisateur test
author, _ = User.objects.get_or_create(
    email="test@example.com",
    defaults={
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
    }
)
author.set_password("admin")
author.save()

# 📊 Statuts disponibles
all_statuses = [status[0] for status in LeadStatus.choices]

# ➕ Création de 300 leads
leads_to_create = []

for _ in range(300):
    status = random.choice(all_statuses)

    lead = Lead(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        phone=fake.phone_number(),
        appointment_date=timezone.now() + timedelta(days=random.randint(-5, 15)) if "RDV" in status else None,
        created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
        status=status,
        assigned_to=author
    )
    leads_to_create.append(lead)

Lead.objects.bulk_create(leads_to_create)
print("✅ 300 leads créés")

# 🗨️ Ajouter des commentaires
leads = Lead.objects.all()
comments_to_create = []

for lead in leads:
    for _ in range(random.randint(0, 4)):
        comments_to_create.append(Comment(
            lead=lead,
            author=author,
            content=fake.paragraph(nb_sentences=random.randint(1, 4)),
            created_at=timezone.now() - timedelta(days=random.randint(0, 10)),
            updated_at=timezone.now()
        ))

Comment.objects.bulk_create(comments_to_create)
print(f"✅ {len(comments_to_create)} commentaires ajoutés")

# 👤 Ajouter les données client (ClientFormData)
client_data_to_create = []

for lead in leads:
    client_data_to_create.append(Client(
        lead=lead,
        civilite=random.choice(list(Civilite)),
        date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=60),
        lieu_naissance=fake.city(),
        pays="France",
        nationalite="Française",
        adresse=fake.street_address(),
        code_postal=fake.postcode(),
        ville=fake.city(),
        date_entree_france=timezone.now().date() - timedelta(days=random.randint(365, 365 * 10)),
        a_un_visa=random.choice([True, False]),
        type_visa=random.choice(list(VisaType)),
        statut_refugie_ou_protection=random.choice([True, False]),
        types_demande=random.sample(list(TypeDemande), k=random.randint(1, 3)),
        demande_deja_formulee=random.choice([True, False]),
        demande_formulee_precise=fake.sentence(nb_words=6),
        situation_familiale=random.choice(list(SituationFamiliale)),
        a_des_enfants=random.choice([True, False]),
        nombre_enfants=random.randint(0, 4),
        nombre_enfants_francais=random.randint(0, 2),
        enfants_scolarises=random.choice([True, False]),
        naissance_enfants_details=fake.text(max_nb_chars=100),
        situation_pro=random.choice(list(SituationProfessionnelle)),
        domaine_activite=fake.job(),
        nombre_fiches_paie=random.randint(0, 3),
        date_depuis_sans_emploi=None,
        a_deja_eu_oqtf=random.choice([True, False]),
        date_derniere_oqtf=None,
        demarche_en_cours_administration=random.choice([True, False]),
        remarques=fake.text(max_nb_chars=200),
    ))

Client.objects.bulk_create(client_data_to_create)
print(f"✅ {len(client_data_to_create)} données client ajoutées")