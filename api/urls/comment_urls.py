from rest_framework.routers import DefaultRouter
from api.views.comment_views import CommentViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = router.urls