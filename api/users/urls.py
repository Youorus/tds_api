# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.users.views import UserViewSet

# Création du routeur principal
router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]