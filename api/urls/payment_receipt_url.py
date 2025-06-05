from rest_framework.routers import DefaultRouter

from api.views.payment_receipt_view import PaymentReceiptViewSet

router = DefaultRouter()
router.register(r"receipts", PaymentReceiptViewSet, basename="receipt")

urlpatterns = router.urls