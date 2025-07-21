from babel.dates import format_datetime
import requests
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

def download_file(url):
    import requests, os
    response = requests.get(url)
    response.raise_for_status()
    content = response.content
    filename = os.path.basename(url)
    return content, filename