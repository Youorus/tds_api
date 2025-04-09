from .auth_urls import urlpatterns as auth_urls
from .lead_urls import urlpatterns as lead_urls
from .comment_urls import urlpatterns as comment_urls
from .email_preview_urls import urlpatterns as email_preview_urls

urlpatterns = [
    *auth_urls,
    *lead_urls,
    *comment_urls,
    *email_preview_urls,
]