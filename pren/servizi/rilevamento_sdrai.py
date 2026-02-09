from dataclasses import dataclass


@dataclass
class SdraioRilevato:
    x_percentuale: float
    y_percentuale: float
    confidenza: float
    classe: str

def rileva_sdrai_da_immagine(percorso_immagine: str):
    """
    Versione di test:
    ritorna sdrai finti per verificare la pipeline.
    """

    return [
        SdraioRilevato(25.0, 30.0, 0.99, "sdraio"),
        SdraioRilevato(60.0, 55.0, 0.95, "sdraio"),
    ]