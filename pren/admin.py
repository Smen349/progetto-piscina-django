from django.contrib import admin
from .models import Piscina, ImmaginePiscina, Sdraio

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

