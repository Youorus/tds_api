from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import DocumentViewSet, DocumentDownloadView

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    path('documents/download/', DocumentDownloadView.as_view(), name='document-download'),
]