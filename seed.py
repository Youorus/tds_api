import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker
from api.models import Lead, User, Comment, LeadStatus

fake = Faker('fr_FR')

# Créer ou récupérer un utilisateur test pour l'auteur des commentaires
author, _ = User.objects.get_or_create(
    email="test@example.com",
    defaults={
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
        "password": "admin",  # à hasher si nécessaire
    }
)

# Liste des statuts pour diversification
all_statuses = [status[0] for status in LeadStatus.choices]

leads_to_create = []
comments_to_create = []

for _ in range(300):  # Génère 300 leads
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
print("✅ Leads créés")

# Récupérer les leads pour y ajouter des commentaires
leads = Lead.objects.all()

for lead in leads:
    for _ in range(random.randint(0, 4)):  # 0 à 4 commentaires par lead
        comments_to_create.append(Comment(
            lead=lead,
            author=author,
            content=fake.paragraph(nb_sentences=random.randint(1, 4)),
            created_at=timezone.now() - timedelta(days=random.randint(0, 10)),
            updated_at=timezone.now()
        ))

Comment.objects.bulk_create(comments_to_create)
print("✅ Commentaires ajoutés")