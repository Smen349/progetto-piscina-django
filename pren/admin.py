from django.contrib import admin
from .models import Piscina, ImmaginePiscina, Sdraio, DurataDisponibile, Prenotazione


@admin.register(DurataDisponibile)
class DurataDisponibileAdmin(admin.ModelAdmin):
    list_display = ("id", "piscina", "tipo", "attiva")
    list_filter = ("piscina", "attiva", "tipo")

@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display = ("id", "utente", "piscina", "sdraio", "tipo_durata", "inizio", "fine", "creata_il")
    list_filter = ("piscina", "tipo_durata")
    ordering = ("-creata_il",)


@admin.register(Piscina)
class PiscinaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "attiva")

    def save_model(self, request, obj, form, change):
        if obj.attiva:
            Piscina.objects.exclude(pk=obj.pk).update(attiva=False)
        super().save_model(request, obj, form, change)


@admin.register(ImmaginePiscina)
class ImmaginePiscinaAdmin(admin.ModelAdmin):
    list_display = ("id", "piscina", "caricata_il")


@admin.register(Sdraio)
class SdraioAdmin(admin.ModelAdmin):
    list_display = ("id", "piscina", "etichetta", "x_percentuale", "y_percentuale", "origine")
    list_filter = ("piscina",)
    search_fields = ("etichetta",)
    readonly_fields = ("origine",)

