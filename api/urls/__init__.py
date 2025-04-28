from .user_urls import urlpatterns as user_urlpatterns
from .auth_urls import urlpatterns as auth_urls
from .lead_urls import urlpatterns as lead_urls
from .comment_urls import urlpatterns as comment_urls
from .email_preview_urls import urlpatterns as email_preview_urls
from .client_urls import urlpatterns as client_urls
from .email_form_urls import urlpatterns as email_urls

urlpatterns = [
    *auth_urls,
    *lead_urls,
    *comment_urls,
    *email_preview_urls,
    *client_urls,
    *email_urls,
    *user_urlpatterns,
]