from rest_framework.routers import DefaultRouter
from api.views import ContractViewSet  # adapte le chemin si besoin

router = DefaultRouter()
router.register(r"contracts", ContractViewSet, basename="contracts")

urlpatterns = router.urls