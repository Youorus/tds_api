from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.custom_auth.views import LoginView

urlpatterns = [
    # Authentification JWT native
    path('token/', TokenObtainPairView.as_view(), name='api_token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    # Authentification "custom" (login par email/mot de passe)
    path("login/", LoginView.as_view(), name="login"),
]