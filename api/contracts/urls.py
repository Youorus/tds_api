# api/contracts/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter

from api.contracts.contract_search import ContractSearchView
from api.contracts.views import ContractViewSet

router = DefaultRouter()
router.register(r'', ContractViewSet, basename='contracts')

urlpatterns = [
    path("search/", ContractSearchView.as_view(), name="contract-search"),
]

urlpatterns += router.urls