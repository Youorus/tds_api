# api/leads/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LeadViewSet
from .lead_search import LeadSearchView

router = DefaultRouter()
router.register(r'', LeadViewSet, basename='leads')

urlpatterns = [
    path("search/", LeadSearchView.as_view(), name="lead-search"),
]

urlpatterns += router.urls