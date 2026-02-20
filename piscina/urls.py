from django.contrib.auth import views as auth_views
from pren.views import signup

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from pren.views import (
    home,
    aggiorna_sdraio,
    prenota_sdraio,
    rigenera_sdrai,
    elimina_sdraio,
    crea_sdraio,
    sdrai_occupati,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("signup/", signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="pren/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("sdrai/<int:sdraio_id>/aggiorna/", aggiorna_sdraio, name="aggiorna_sdraio"),
    path("sdrai/<int:sdraio_id>/elimina/", elimina_sdraio, name="elimina_sdraio"),
    path("sdrai/crea/<int:piscina_id>/", crea_sdraio, name="crea_sdraio"),

    path("prenota/<int:sdraio_id>/", prenota_sdraio, name="prenota_sdraio"),
    path("rigenera/<int:piscina_id>/", rigenera_sdrai, name="rigenera_sdrai"),

    path("api/occupati/<int:piscina_id>/", sdrai_occupati, name="sdrai_occupati"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)