# check_db.py
import os

import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tds.settings")
django.setup()

try:
    connection.ensure_connection()
    print("✅ Connexion à la DB Render réussie!")
    print(f"DB utilisée : {connection.settings_dict['NAME']}")
    print(f"Host : {connection.settings_dict['HOST']}")
except Exception as e:
    print("❌ Échec de connexion à la DB :")
    print(str(e))
