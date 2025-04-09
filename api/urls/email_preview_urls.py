from django.urls import path

from api.views import email_preview

urlpatterns = [
    path("preview/email/welcome/", email_preview.preview_welcome_email),
    path("preview/email/confirmation/", email_preview.preview_appointment_confirmation),
    path("preview/email/reminder/", email_preview.preview_appointment_reminder),
]