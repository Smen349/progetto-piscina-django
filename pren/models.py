from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
