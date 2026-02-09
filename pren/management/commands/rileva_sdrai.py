from django.core.management.base import BaseCommand
from pren.models import Piscina, Sdraio
from pren.servizi.rilevamento_sdrai import rileva_sdrai_da_immagine


class Command(BaseCommand):
    help = "Rileva sdrai (ver test) e stampa le coordinate"

    def add_arguments(self, parser):
        parser.add_argument("piscina_id", type=int)
        parser.add_argument("--pulisci", action="store_true", help="Cancella gli sdrai esistenti prima di crearli")
        parser.add_argument("--solo-stampa", action="store_true", help="Non salva nel DB, stampa soltanto") 

    def handle(self, *args, **options):
        piscina_id = options["piscina_id"]
        pulisci = options["pulisci"]
        solo_stampa = options["solo_stampa"]

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

        if solo_stampa:
            self.stdout.write(self.style.WARNING("Modalità solo-stampa: nessun salvataggio nel DB"))
            return

        if pulisci:
            cancellati = Sdraio.objects.filter(piscina=piscina, origine="AI").delete()[0]
            self.stdout.write(self.style.WARNING(f"Cancellati {cancellati} sdrai esistenti"))

        creati = 0
        for idx, s in enumerate(sdrai, start=1):
            Sdraio.objects.create(
                piscina=piscina,
                etichetta=f"AI-{idx}",
                x_percentuale=s.x_percentuale,
                y_percentuale=s.y_percentuale,
                origine="AI",
            )
            creati += 1
        
        self.stdout.write(self.style.SUCCESS(f"Creati {creati} sdrai nel DB"))



