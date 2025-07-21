from rest_framework.routers import DefaultRouter

from api.payments.views import PaymentReceiptViewSet

router = DefaultRouter()
router.register(r"", PaymentReceiptViewSet, basename="receipts")

urlpatterns = router.urls