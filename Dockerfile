# ─── STAGE 1 : Builder ─────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer dépendances système nécessaires à la compilation et à wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ Étape de cache 1 : requirements.txt
COPY requirements.txt .

# ✅ Étape de cache 2 : installation des dépendances Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# ⛔️ Étape sensible : copier tout le code source
COPY . .



# ─── STAGE 2 : Final ───────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer uniquement les dépendances nécessaires à wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ Copier les packages Python installés depuis le builder
COPY --from=builder /usr/local /usr/local

# ✅ Copier le projet (application Django)
COPY --from=builder /app /app

EXPOSE 8000

CMD ["gunicorn", "tds.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]