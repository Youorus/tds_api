from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views.auth_views import LoginView
from api.views.me_view import MeView  # on importe la vue MeView

urlpatterns = [
    #  Authentification
    path('token/', TokenObtainPairView.as_view(), name='api_token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path("login/", LoginView.as_view(), name="login"),

    # 👤 Utilisateur connecté
    path("me/", MeView.as_view(), name="me"),  # nouvelle route
]