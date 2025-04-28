from django.urls import path
from api.views import SendFormulaireEmailView

urlpatterns = [
    path("send-formulaire-email/", SendFormulaireEmailView.as_view(), name="send_formulaire_email"),
]