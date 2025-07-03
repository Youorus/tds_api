import re
from urllib.parse import urlparse

import unicodedata
from babel.dates import format_datetime
from django.core.files.storage import default_storage
from django.utils import timezone

def get_formatted_appointment(dt):
    if not dt:
        return {
            "date": "Non précisée",
            "time": "Non précisée"
        }

    local_dt = timezone.localtime(dt)

    return {
        "date": format_datetime(local_dt, "EEEE d MMMM y", locale="fr").capitalize(),  # ex: lundi 10 avril 2025
        "time": format_datetime(local_dt, "HH:mm", locale="fr"),                       # ex: 14:30
    }
