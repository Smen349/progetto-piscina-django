from django.core.management.base import BaseCommand
from pren.models import Piscina
from pren.servizi.rilevamento_sdrai import rileva_sdrai_da_immagine


class Command(BaseCommand):
    help = "Rileva sdrai (ver test) e stampa le coordinate"

    def add_arguments(self, parser):
        parser.add_argument("piscina_id", type=int)

    def handle(self, *args, **options):
        piscina_id = options["piscina_id"]
        piscina = Piscina.objects.get(id=piscina_id)
        percorso_img = piscina.immagine.immagine.path
        sdrai = rileva_sdrai_da_immagine(percorso_img)

        self.stdout.write(self.style.SUCCESS(
            f"Trovati {len(sdrai)} sdrai"
        ))

        for s in sdrai:
            self.stdout.write(
                f"- {s.classe} x={s.x_percentuale}% y={s.y_percentuale}% conf={s.confidenza}"
            )
