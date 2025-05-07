# api/urls/avatar_urls.py

from rest_framework.routers import DefaultRouter

from api.views.user_avatar_views import UserAvatarViewSet

router = DefaultRouter()
router.register(r'avatars', UserAvatarViewSet, basename='user-avatar')

urlpatterns = router.urls