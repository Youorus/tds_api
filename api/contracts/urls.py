# api/contracts/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from api.contracts.views import ContractViewSet
from api.contracts.contract_search import ContractSearchAPIView

router = DefaultRouter()
router.register(r'', ContractViewSet, basename='contracts')

urlpatterns = [
    path("search/", ContractSearchAPIView.as_view(), name="contract-search"),
]

urlpatterns += router.urls