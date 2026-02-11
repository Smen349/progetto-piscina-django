
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from pren.views import home, aggiorna_sdraio

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("sdrai/<int:sdraio_id>/aggiorna/", aggiorna_sdraio, name="aggiorna_sdraio"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    