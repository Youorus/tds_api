# ─── STAGE 1 : Builder ─────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier le projet entier (y compris tools/wkhtmltopdf)
COPY . .

# Rendre le binaire wkhtmltopdf exécutable si nécessaire
RUN chmod +x tools/wkhtmltopdf

# Ajouter wkhtmltopdf au PATH global
ENV PATH="/app/tools:$PATH"


# ─── STAGE 2 : Final ───────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copier tout le dossier du builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Rendre wkhtmltopdf utilisable dans l'image finale
ENV PATH="/app/tools:$PATH"

# Collecte des fichiers statiques (si applicable)
RUN python manage.py collectstatic --noinput

# Exposer le port (si tu utilises Gunicorn)
EXPOSE 8000

# Lancement avec Gunicorn + Uvicorn worker pour ASGI
CMD ["gunicorn", "tds.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]