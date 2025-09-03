# ─── STAGE 1 : Builder ─────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier le projet
COPY . .

# Lancer les tests (facultatif mais conseillé)
# RUN pytest || exit 1

# ─── STAGE 2 : Final ───────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copier deps du builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port
EXPOSE 8000

# Lancement avec gunicorn/uvicorn
CMD ["gunicorn", "tds.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]