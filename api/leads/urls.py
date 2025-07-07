# api/urls.py

from rest_framework.routers import DefaultRouter

from api.leads.views import LeadViewSet

# Utilise des imports explicites par vue pour une architecture modulaire claire

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='leads')

urlpatterns = router.urls

# Astuce : si tu as d'autres routes à ajouter (actions custom), utilise des fichiers urls complémentaires