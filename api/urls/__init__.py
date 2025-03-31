from django.urls import path, include

from .auth_urls import urlpatterns as auth_urls
from .lead_urls import urlpatterns as lead_urls
# import d’autres modules au besoin

urlpatterns = [
    *auth_urls,
    *lead_urls,
]