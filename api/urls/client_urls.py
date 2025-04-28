from rest_framework.routers import DefaultRouter
from api.views.client_views import ClientViewSet

router = DefaultRouter()
router.register(r"clients", ClientViewSet, basename="clients")

urlpatterns = router.urls