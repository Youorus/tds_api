from rest_framework.routers import DefaultRouter

from api.payments.views import PaymentReceiptViewSet

router = DefaultRouter()
router.register(r"receipts", PaymentReceiptViewSet, basename="receipt")

urlpatterns = router.urls