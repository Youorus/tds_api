from rest_framework.routers import DefaultRouter
from api.views import PaymentViewSet  # adapte le chemin si besoin

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls