from rest_framework.routers import DefaultRouter
from api.documents.views import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
urlpatterns = router.urls