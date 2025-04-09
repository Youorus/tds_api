from datetime import datetime

from django.shortcuts import render
from django.contrib.auth import get_user_model

User = get_user_model()

def preview_welcome_email(request):
    user = User.objects.first()  # ⚠️ pour test, prends le premier user
    return render(request, "email/welcome.html", {
        "user": user,
        "year": datetime.now().year,
    })

def preview_appointment_confirmation(request):
    user = User.objects.first()
    appointment = {
        "date": "2025-04-15",
        "time": "14:30",
        "location": "11 rue de l'Arrivée, 75015 Paris",
    }
    return render(request, "email/appointment_confirmation.html", {
        "user": user,
        "appointment": appointment,
        "year": datetime.now().year,
    })

def preview_appointment_reminder(request):
    user = User.objects.first()
    appointment = {
        "date": "2025-04-16",
        "time": "10:00",
        "location": "11 rue de l'Arrivée, 75015 Paris ( face au magasin CA de l'interieur)",
    }
    return render(request, "email/appointment_reminder.html", {
        "user": user,
        "appointment": appointment,
        "year": datetime.now().year,
    })