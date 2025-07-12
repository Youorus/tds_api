from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # 👈 tu inclus tout ce qui est dans api/urls/
    path("api/", include("api.custom_auth.urls")),
]