# api/urls.py

from rest_framework.routers import DefaultRouter

from api.leads.views import LeadViewSet

# Utilise des imports explicites par vue pour une architecture modulaire claire

router = DefaultRouter()
router.register(r'', LeadViewSet, basename='leads')

urlpatterns = router.urls
