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

# ✅ Étape de cache 1 : requirements.txt (rarement modifié)
COPY requirements.txt .

# ✅ Étape de cache 2 : installation pip
RUN pip install --upgrade pip && pip install -r requirements.txt

# ⛔️ Étape sensible : copier le projet (change souvent → invalide le cache)
COPY . .

# wkhtmltopdf binaire interne
RUN chmod +x tools/wkhtmltopdf

# Mettre dans le PATH
ENV PATH="/app/tools:$PATH"


# ─── STAGE 2 : Final ───────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ✅ Copier /usr/local (pip install déjà fait)
COPY --from=builder /usr/local /usr/local

# ✅ Copier ton app et wkhtmltopdf
COPY --from=builder /app /app

# wkhtmltopdf dans le PATH
ENV PATH="/app/tools:$PATH"

EXPOSE 8000

CMD ["gunicorn", "tds.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]