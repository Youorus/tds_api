from django.urls import path, include
from .auth_urls import urlpatterns as auth_urls
from .lead_urls import urlpatterns as lead_urls
from .comment_urls import urlpatterns as comment_urls  # Correction de l'import

urlpatterns = [
    *auth_urls,
    *lead_urls,
    *comment_urls,  # Correction de la faute de frappe (commment -> comment)
    # Vous pouvez aussi utiliser include() pour plus de clarté :
    # path('', include('api.auth_urls')),
    # path('', include('api.lead_urls')),
    # path('', include('api.comment_urls')),
]