from rest_framework.routers import DefaultRouter
from api.views.lead_views import LeadViewSet

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='leads')

urlpatterns = router.urls