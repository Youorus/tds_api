from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.client_views import ClientViewSet

router = DefaultRouter()
router.register(r"clients", ClientViewSet, basename="clients")

urlpatterns = [
    path("", include(router.urls)),
]