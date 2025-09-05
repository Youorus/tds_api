from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .me_views import MeView
from .views import UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="users")

urlpatterns = [
    re_path(r"^me$", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
