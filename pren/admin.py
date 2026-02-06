from django.contrib import admin
from .models import Piscina, ImmaginePiscina, Sdraio

@admin.register(Piscina)
class PiscinaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")


@admin.register(ImmaginePiscina)
class ImmaginePiscinaAdmin(admin.ModelAdmin):
    list_display = ("id", "piscina", "caricata_il")


@admin.register(Sdraio)
class SdraioAdmin(admin.ModelAdmin):
    list_display = ("id", "piscina", "etichetta", "x_percentuale", "y_percentuale")
    list_filter = ("piscina",)
    search_fields = ("etichetta",)

