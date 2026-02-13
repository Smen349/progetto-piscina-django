from django.core.management.base import BaseCommand
from pren.models import Piscina, Sdraio
from pren.servizi.rilevamento_sdrai import rileva_sdrai_da_immagine


class Command(BaseCommand):
    help = "Rileva sdrai (ver test) e stampa le coordinate"

    def add_arguments(self, parser):
        parser.add_argument("piscina_id", type=int)
        parser.add_argument("--pulisci", action="store_true", help="Cancella solo gli sdrai con origine=AI prima di crearli")
        parser.add_argument("--solo-stampa", action="store_true", help="Non salva nel DB, stampa soltanto")
        parser.add_argument("--conf", type=float, default=0.20, help="Soglia minima confidenza YOLO")

    def handle(self, *args, **options):
        piscina_id = options["piscina_id"]
        pulisci = options["pulisci"]
        solo_stampa = options["solo_stampa"]
        conf = options["conf"]

        try:
            piscina = Piscina.objects.get(id=piscina_id)
        except Piscina.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Piscina id={piscina_id} non trovata"))
            return

        if not hasattr(piscina, "immagine") or not piscina.immagine.immagine:
            self.stdout.write(self.style.ERROR("Questa piscina non ha un'immagine associata."))
            return

        percorso_img = piscina.immagine.immagine.path


        if pulisci:
            cancellati = Sdraio.objects.filter(piscina=piscina, origine="AI").delete()[0]
            self.stdout.write(self.style.WARNING(f"Cancellati {cancellati} sdrai esistenti"))


        sdrai = rileva_sdrai_da_immagine(percorso_img, conf_min=conf)

        self.stdout.write(self.style.SUCCESS(
        f"Piscina: {piscina.nome} (id={piscina.id}) | conf_min={conf}"
        ))
        self.stdout.write(f"Rilevati: {len(sdrai)}")


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

        
        creati = 0
        saltati = 0
        base = Sdraio.objects.filter(piscina=piscina, origine="AI").count()
        
        for idx, s in enumerate(sdrai, start=base + 1):
            esiste = Sdraio.objects.filter(
                piscina=piscina,
                origine="AI",
                x_percentuale__range=(s.x_percentuale - 1, s.x_percentuale + 1),
                y_percentuale__range=(s.y_percentuale - 1, s.y_percentuale + 1),
            ).exists()
            
            if esiste:
                saltati += 1
                continue

            Sdraio.objects.create(
                piscina=piscina,
                etichetta=f"AI-{idx}",
                x_percentuale=s.x_percentuale,
                y_percentuale=s.y_percentuale,
                origine="AI",
            )
            creati += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Creati: {creati} | Duplicati saltati: {saltati}"
        ))



