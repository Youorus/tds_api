# urls.py

from .views import OpeningHoursViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'', OpeningHoursViewSet, basename='opening-hours')

urlpatterns = router.urls
