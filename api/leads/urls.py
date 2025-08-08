from django.urls import path
from rest_framework.routers import DefaultRouter

from api.leads.lead_search import LeadSearchAPIView
from api.leads.views import LeadViewSet

router = DefaultRouter()
router.register(r'', LeadViewSet, basename='leads')

urlpatterns = [
    # Tes endpoints "custom" ici AVANT le router.urls
    path('search/', LeadSearchAPIView.as_view(), name="lead-search"),
]

urlpatterns += router.urls  # On ajoute toutes les routes du ViewSet après