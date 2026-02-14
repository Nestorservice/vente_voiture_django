from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("inventory.urls")),  # Ton application de voitures
]

# Servir les fichiers media (images) en local ET en production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
