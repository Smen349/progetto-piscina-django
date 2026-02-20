from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class TipoDurata(models.TextChoices):
    ORA_1 = "1H", "1 ora"
    ORE_3 = "2_3H", "3 ore"
    MEZZA_GIORNATA = "HALF", "Mezza giornata"
    GIORNATA_INTERA = "FULL", "Intera giornata"


DURATA_MINUTI = {
    TipoDurata.ORA_1: 60,
    TipoDurata.ORE_3: 180,
    TipoDurata.MEZZA_GIORNATA: 240,
    TipoDurata.GIORNATA_INTERA: 480,
}


class DurataDisponibile(models.Model):
    piscina = models.ForeignKey("Piscina", on_delete=models.CASCADE, related_name="durate_disponibili")
    tipo = models.CharField(max_length=10, choices=TipoDurata.choices)
    attiva = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["piscina", "tipo"], name="uniq_durata_per_piscina")
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} ({'attiva' if self.attiva else 'non attiva'})"


class Prenotazione(models.Model):
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prenotazioni")
    sdraio = models.ForeignKey("Sdraio", on_delete=models.CASCADE, related_name="prenotazioni")
    piscina = models.ForeignKey("Piscina", on_delete=models.CASCADE, related_name="prenotazioni")
    tipo_durata = models.CharField(max_length=10, choices=TipoDurata.choices)
    inizio = models.DateTimeField()
    fine = models.DateTimeField(editable=False)
    creata_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sdraio", "inizio"], name="uniq_sdraio_inizio"),
        ]

    def clean(self):
        if not self.inizio:
            raise ValidationError("Devi scegliere una data/ora di inizio.")

        # ✅ blocco prenotazione nel passato
        if timezone.is_naive(self.inizio):
            self.inizio = timezone.make_aware(self.inizio)

        now = timezone.now()
        if self.inizio < now:
            raise ValidationError("Non puoi prenotare nel passato.")

        minuti = DURATA_MINUTI.get(self.tipo_durata)
        if minuti is None:
            raise ValidationError("Tipo durata non valido.")

        self.fine = self.inizio + timedelta(minutes=minuti)

        conflitto = Prenotazione.objects.filter(
            sdraio=self.sdraio,
            inizio__lt=self.fine,
            fine__gt=self.inizio,
        )
        if self.pk:
            conflitto = conflitto.exclude(pk=self.pk)

        if conflitto.exists():
            raise ValidationError("Questo sdraio è già prenotato nel periodo selezionato.")

    def save(self, *args, **kwargs):
        self.full_clean()  # calcola fine + controlla conflitti + passato
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.utente} -> {self.sdraio} {self.get_tipo_durata_display()} {self.inizio:%d/%m %H:%M}-{self.fine:%H:%M}"


class Piscina(models.Model):
    nome = models.CharField(max_length=120)
    attiva = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class ImmaginePiscina(models.Model):
    piscina = models.OneToOneField(
        Piscina,
        on_delete=models.CASCADE,
        related_name="immagine"
    )

    immagine = models.ImageField(upload_to="immagini_piscine/")
    caricata_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Immagine - {self.piscina.nome}"


class Sdraio(models.Model):
    ORIGINE_SCELTE = [
        ("AI", "Rilevamento automatico"),
        ("MANUALE", "Inserito manualmente"),
    ]

    piscina = models.ForeignKey(
        Piscina,
        on_delete=models.CASCADE,
        related_name="sdrai"
    )

    etichetta = models.CharField(max_length=50, blank=True, default="")

    x_percentuale = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0
    )

    y_percentuale = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0
    )

    origine = models.CharField(
        max_length=10,
        choices=ORIGINE_SCELTE,
        default="MANUALE",
    )

    def __str__(self):
        return f"{self.piscina.nome} - {self.etichetta or f'Sdraio #{self.pk}'}"