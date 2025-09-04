# ─── STAGE 1 : Builder ─────────────────────────────
FROM python:3.11-slim AS builder

# Environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier tout le projet
COPY . .

# Lancer les tests (le build s'arrête si un test échoue)
RUN pip install pytest && pytest --disable-warnings || exit 1

# ─── STAGE 2 : Final ───────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copier les dépendances Python installées depuis le builder
COPY --from=builder /usr/local /usr/local

# Copier l'application
COPY --from=builder /app /app

# Collecte des fichiers statiques (optionnel pour une API)
RUN python manage.py collectstatic --noinput

# Exposer le port utilisé par Gunicorn
EXPOSE 8000

# Commande de lancement de l'application ASGI avec Gunicorn + Uvicorn worker
CMD ["gunicorn", "tds.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]