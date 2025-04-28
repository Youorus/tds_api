#!/bin/bash

# 🔧 Variables de configuration
DB_NAME="tds"
DB_USER="marc"
DB_PASSWORD="marc"   # ← remplace ici par le vrai mot de passe de l'utilisateur marc
DB_HOST="localhost"
DB_PORT="5432"

# Export du mot de passe pour éviter le prompt
export PGPASSWORD=$DB_PASSWORD

echo "⚠️  Réinitialisation complète de la base : $DB_NAME"

# 🧨 Suppression de la base (on se connecte à 'postgres' pour pouvoir la drop)
echo "🗑️  Suppression de la base $DB_NAME..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# 🛠️ Création de la nouvelle base
echo "🆕 Création de la base $DB_NAME..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d postgres -c "CREATE DATABASE $DB_NAME;"

# 🚿 Nettoyage des anciennes migrations (optionnel mais conseillé en dev)
echo "🧹 Suppression des anciennes migrations..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 🧱 Recréer les migrations
echo "📦 Création des migrations..."
python manage.py makemigrations

# 🚀 Appliquer les migrations sur la nouvelle DB
echo "⚙️  Application des migrations..."
python manage.py migrate

echo "✅ Base de données $DB_NAME réinitialisée avec succès."