from rest_framework.routers import DefaultRouter

from api.views import LeadStatusViewSet, StatusDossierViewSet
from api.views.lead_views import LeadViewSet

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='leads')
router.register(r'lead-statuses', LeadStatusViewSet, basename='lead-statuses')
router.register(r'statut-dossiers', StatusDossierViewSet, basename='statut-dossiers')
urlpatterns = router.urls