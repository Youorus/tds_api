# api/payments/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.payments.receipt_search import PaymentReceiptSearchAPIView
from api.payments.views import PaymentReceiptViewSet

router = DefaultRouter()
router.register(r"", PaymentReceiptViewSet, basename="receipts")

urlpatterns = [
    path("search/", PaymentReceiptSearchAPIView.as_view(), name="receipts-search"),
    path("", include(router.urls)),
]